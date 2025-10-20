"""
Advanced RAG retrieval system with agentic workflows using LangGraph.
Implements iterative reasoning, self-correction, and hallucination prevention.
"""

from typing import List, Dict, Any, Optional, TypedDict
from uuid import UUID

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from qdrant_client.models import Filter, FieldCondition, MatchValue

from config import settings
from rag.embeddings import EmbeddingService


class AgentState(TypedDict):
    """State for the RAG agent workflow."""
    query: str
    patient_id: Optional[str]
    clinic_id: Optional[str]
    decomposed_queries: List[str]
    retrieved_docs: List[Dict[str, Any]]
    verified_docs: List[Dict[str, Any]]
    answer: str
    citations: List[Dict[str, Any]]
    confidence_score: float
    needs_refinement: bool
    iteration_count: int


class AgenticRAG:
    """
    Agentic RAG system with LangGraph for medical knowledge retrieval.
    Features:
    - Query decomposition for complex questions
    - Iterative retrieval and verification
    - Hallucination detection
    - Citation tracking
    - Self-correction
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",
        collection_name: str = "medical_knowledge"
    ) -> None:
        """
        Initialize agentic RAG system.
        
        Args:
            llm_provider: LLM provider (openai or anthropic)
            collection_name: Qdrant collection name
        """
        self.collection_name = collection_name
        self.embedding_service = EmbeddingService()
        
        # Initialize LLM
        if llm_provider == "openai":
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0.1,  # Low temperature for factual responses
                openai_api_key=settings.openai_api_key
            )
        elif llm_provider == "anthropic":
            self.llm = ChatAnthropic(
                model=settings.anthropic_model,
                temperature=0.1,
                anthropic_api_key=settings.anthropic_api_key
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
        
        # Build the agent workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow for agentic RAG.
        
        Returns:
            Compiled StateGraph workflow
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("decompose_query", self._decompose_query)
        workflow.add_node("retrieve", self._retrieve_documents)
        workflow.add_node("verify", self._verify_documents)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("check_quality", self._check_quality)
        workflow.add_node("refine", self._refine_answer)
        
        # Define edges
        workflow.set_entry_point("decompose_query")
        workflow.add_edge("decompose_query", "retrieve")
        workflow.add_edge("retrieve", "verify")
        workflow.add_edge("verify", "generate_answer")
        workflow.add_edge("generate_answer", "check_quality")
        
        # Conditional edge: refine if needed, else end
        workflow.add_conditional_edges(
            "check_quality",
            self._should_refine,
            {
                True: "refine",
                False: END
            }
        )
        workflow.add_edge("refine", "retrieve")  # Loop back for refinement
        
        return workflow.compile()
    
    async def _decompose_query(self, state: AgentState) -> AgentState:
        """
        Decompose complex query into sub-questions.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with decomposed queries
        """
        decomposition_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a medical query analyst. Break down complex medical 
            questions into simpler, focused sub-questions that can be answered independently. 
            Each sub-question should target a specific aspect of the original question."""),
            HumanMessage(content=f"Decompose this medical query: {state['query']}")
        ])
        
        response = await self.llm.ainvoke(decomposition_prompt.format_messages())
        
        # Parse sub-questions (assuming LLM returns numbered list)
        sub_queries = [
            line.strip().lstrip("0123456789.-) ")
            for line in response.content.split("\n")
            if line.strip() and any(c.isalpha() for c in line)
        ]
        
        state["decomposed_queries"] = sub_queries if sub_queries else [state["query"]]
        state["iteration_count"] = 0
        
        return state
    
    async def _retrieve_documents(self, state: AgentState) -> AgentState:
        """
        Retrieve relevant documents for each sub-query.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with retrieved documents
        """
        all_docs = []
        
        for sub_query in state["decomposed_queries"]:
            # Build filters for patient-specific and clinic-specific data
            filters = None
            if state.get("patient_id") or state.get("clinic_id"):
                conditions = []
                if state.get("patient_id"):
                    conditions.append(
                        FieldCondition(
                            key="patient_id",
                            match=MatchValue(value=state["patient_id"])
                        )
                    )
                if state.get("clinic_id"):
                    conditions.append(
                        FieldCondition(
                            key="clinic_id",
                            match=MatchValue(value=state["clinic_id"])
                        )
                    )
                if conditions:
                    filters = Filter(must=conditions)
            
            # Perform hybrid search
            results = await self.embedding_service.search(
                collection_name=self.collection_name,
                query=sub_query,
                limit=5,
                score_threshold=0.7,
                filters=filters
            )
            
            all_docs.extend(results)
        
        # Deduplicate by document ID
        unique_docs = {doc["id"]: doc for doc in all_docs}.values()
        state["retrieved_docs"] = list(unique_docs)
        
        return state
    
    async def _verify_documents(self, state: AgentState) -> AgentState:
        """
        Verify retrieved documents for relevance and accuracy.
        Implements hallucination prevention.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with verified documents
        """
        verification_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a medical information verifier. Assess whether each 
            document is relevant and accurate for answering the query. Consider medical accuracy, 
            recency, and source credibility. Return a JSON list of document IDs that pass verification."""),
            HumanMessage(content=f"""Query: {state['query']}
            
Documents:
{chr(10).join([f"ID: {doc['id']}, Content: {doc['payload'].get('text', '')}..." for doc in state['retrieved_docs']])}

Return only the IDs of verified documents as a JSON array.""")
        ])
        
        response = await self.llm.ainvoke(verification_prompt.format_messages())
        
        # Parse verified document IDs
        try:
            import json
            verified_ids = json.loads(response.content)
            state["verified_docs"] = [
                doc for doc in state["retrieved_docs"]
                if doc["id"] in verified_ids
            ]
        except:
            # If parsing fails, use all retrieved docs
            state["verified_docs"] = state["retrieved_docs"]
        
        return state
    
    async def _generate_answer(self, state: AgentState) -> AgentState:
        """
        Generate answer based on verified documents.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with generated answer and citations
        """
        # Prepare context from verified documents
        context = "\n\n".join([
            f"[Source {idx+1}] {doc['payload'].get('text', '')}"
            for idx, doc in enumerate(state["verified_docs"])
        ])
        
        answer_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a medical information assistant. Provide accurate, 
            evidence-based answers using ONLY the information from the provided sources. Include 
            citations using [Source N] format. If the sources don't contain enough information, 
            state that clearly. Do not make assumptions or add information not in the sources."""),
            HumanMessage(content=f"""Question: {state['query']}
            
Context:
{context}

Provide a comprehensive answer with citations.""")
        ])
        
        response = await self.llm.ainvoke(answer_prompt.format_messages())
        
        state["answer"] = response.content
        state["citations"] = [
            {
                "source_id": doc["id"],
                "content": doc["payload"].get("text", ""),
                "score": doc["score"],
                "metadata": doc["payload"]
            }
            for doc in state["verified_docs"]
        ]
        
        return state
    
    async def _check_quality(self, state: AgentState) -> AgentState:
        """
        Check quality of generated answer for hallucinations and completeness.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with quality assessment
        """
        quality_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a quality assessor for medical information. Evaluate 
            the answer for: 1) Factual accuracy based on sources, 2) Completeness, 3) Presence of 
            unsupported claims. Return a JSON with "confidence_score" (0-1), "needs_refinement" (boolean), 
            and "issues" (list of problems)."""),
            HumanMessage(content=f"""Question: {state['query']}
Answer: {state['answer']}
Sources: {len(state['verified_docs'])}

Evaluate this answer.""")
        ])
        
        response = await self.llm.ainvoke(quality_prompt.format_messages())
        
        try:
            import json
            assessment = json.loads(response.content)
            state["confidence_score"] = assessment.get("confidence_score", 0.8)
            state["needs_refinement"] = assessment.get("needs_refinement", False)
        except:
            # Default to accepting answer
            state["confidence_score"] = 0.8
            state["needs_refinement"] = False
        
        state["iteration_count"] += 1
        
        return state
    
    def _should_refine(self, state: AgentState) -> bool:
        """
        Determine if answer needs refinement.
        
        Args:
            state: Current agent state
            
        Returns:
            True if refinement needed, False otherwise
        """
        # Refine if quality check failed and haven't exceeded max iterations
        return state["needs_refinement"] and state["iteration_count"] < 3
    
    async def _refine_answer(self, state: AgentState) -> AgentState:
        """
        Refine query for better retrieval in next iteration.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with refined query
        """
        refinement_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a query refinement specialist. Based on the current 
            answer's deficiencies, generate an improved query that will retrieve better sources."""),
            HumanMessage(content=f"""Original query: {state['query']}
Current answer quality: {state['confidence_score']}

Generate a refined query for better results.""")
        ])
        
        response = await self.llm.ainvoke(refinement_prompt.format_messages())
        
        # Add refined query to decomposed queries
        state["decomposed_queries"].append(response.content.strip())
        
        return state
    
    async def query(
        self,
        question: str,
        patient_id: Optional[UUID] = None,
        clinic_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Execute agentic RAG query.
        
        Args:
            question: User's question
            patient_id: Optional patient context
            clinic_id: Optional clinic context
            
        Returns:
            Dict with answer, citations, and confidence score
        """
        initial_state: AgentState = {
            "query": question,
            "patient_id": str(patient_id) if patient_id else None,
            "clinic_id": str(clinic_id) if clinic_id else None,
            "decomposed_queries": [],
            "retrieved_docs": [],
            "verified_docs": [],
            "answer": "",
            "citations": [],
            "confidence_score": 0.0,
            "needs_refinement": False,
            "iteration_count": 0
        }
        
        # Run the workflow
        final_state = await self.workflow.ainvoke(initial_state)
        
        return {
            "answer": final_state["answer"],
            "citations": final_state["citations"],
            "confidence_score": final_state["confidence_score"],
            "iterations": final_state["iteration_count"]
        }

