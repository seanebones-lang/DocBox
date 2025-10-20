"""
Neo4j graph database client for managing healthcare relationships.
Tracks patient-doctor-clinic relationships, referrals, and care pathways.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable

from config import settings


class Neo4jClient:
    """
    Async Neo4j client for healthcare graph operations.
    Manages complex relationships between patients, doctors, clinics, and medical events.
    """
    
    def __init__(self) -> None:
        """Initialize Neo4j driver."""
        self.driver: Optional[AsyncDriver] = None
        self._initialize_driver()
    
    def _initialize_driver(self) -> None:
        """Create async Neo4j driver instance."""
        self.driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_lifetime=3600,
            max_connection_pool_size=50,
            connection_acquisition_timeout=120,
        )
    
    async def verify_connectivity(self) -> bool:
        """
        Verify connection to Neo4j database.
        Returns True if connected successfully.
        """
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as num")
                record = await result.single()
                return record["num"] == 1
        except ServiceUnavailable as e:
            print(f"Neo4j connection failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close Neo4j driver connection."""
        if self.driver:
            await self.driver.close()
    
    async def create_indexes(self) -> None:
        """
        Create indexes and constraints for optimal query performance.
        Should be run during initial setup.
        """
        async with self.driver.session() as session:
            # Patient constraints and indexes
            await session.run(
                "CREATE CONSTRAINT patient_id_unique IF NOT EXISTS "
                "FOR (p:Patient) REQUIRE p.id IS UNIQUE"
            )
            await session.run(
                "CREATE INDEX patient_mrn IF NOT EXISTS "
                "FOR (p:Patient) ON (p.medical_record_number)"
            )
            
            # Doctor constraints and indexes
            await session.run(
                "CREATE CONSTRAINT doctor_id_unique IF NOT EXISTS "
                "FOR (d:Doctor) REQUIRE d.id IS UNIQUE"
            )
            
            # Clinic constraints and indexes
            await session.run(
                "CREATE CONSTRAINT clinic_id_unique IF NOT EXISTS "
                "FOR (c:Clinic) REQUIRE c.id IS UNIQUE"
            )
            
            # Appointment constraints
            await session.run(
                "CREATE CONSTRAINT appointment_id_unique IF NOT EXISTS "
                "FOR (a:Appointment) REQUIRE a.id IS UNIQUE"
            )
            
            # Diagnosis constraints
            await session.run(
                "CREATE CONSTRAINT diagnosis_id_unique IF NOT EXISTS "
                "FOR (d:Diagnosis) REQUIRE d.id IS UNIQUE"
            )
            
            # Medication constraints
            await session.run(
                "CREATE CONSTRAINT medication_id_unique IF NOT EXISTS "
                "FOR (m:Medication) REQUIRE m.id IS UNIQUE"
            )
    
    # ==================== PATIENT OPERATIONS ====================
    
    async def create_patient_node(
        self,
        patient_id: UUID,
        medical_record_number: str,
        name: str,
        **properties: Any
    ) -> Dict[str, Any]:
        """Create a patient node in the graph."""
        async with self.driver.session() as session:
            query = """
            CREATE (p:Patient {
                id: $patient_id,
                medical_record_number: $mrn,
                name: $name,
                created_at: datetime()
            })
            RETURN p
            """
            result = await session.run(
                query,
                patient_id=str(patient_id),
                mrn=medical_record_number,
                name=name,
                **properties
            )
            record = await result.single()
            return dict(record["p"]) if record else {}
    
    async def create_doctor_node(
        self,
        doctor_id: UUID,
        name: str,
        specialty: str,
        **properties: Any
    ) -> Dict[str, Any]:
        """Create a doctor node in the graph."""
        async with self.driver.session() as session:
            query = """
            CREATE (d:Doctor {
                id: $doctor_id,
                name: $name,
                specialty: $specialty,
                created_at: datetime()
            })
            RETURN d
            """
            result = await session.run(
                query,
                doctor_id=str(doctor_id),
                name=name,
                specialty=specialty,
                **properties
            )
            record = await result.single()
            return dict(record["d"]) if record else {}
    
    async def create_clinic_node(
        self,
        clinic_id: UUID,
        name: str,
        code: str,
        **properties: Any
    ) -> Dict[str, Any]:
        """Create a clinic node in the graph."""
        async with self.driver.session() as session:
            query = """
            CREATE (c:Clinic {
                id: $clinic_id,
                name: $name,
                code: $code,
                created_at: datetime()
            })
            RETURN c
            """
            result = await session.run(
                query,
                clinic_id=str(clinic_id),
                name=name,
                code=code,
                **properties
            )
            record = await result.single()
            return dict(record["c"]) if record else {}
    
    # ==================== RELATIONSHIP OPERATIONS ====================
    
    async def create_treats_relationship(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        since: str = None
    ) -> bool:
        """Create TREATS relationship between doctor and patient."""
        async with self.driver.session() as session:
            query = """
            MATCH (d:Doctor {id: $doctor_id})
            MATCH (p:Patient {id: $patient_id})
            MERGE (d)-[r:TREATS {since: coalesce($since, datetime())}]->(p)
            RETURN r
            """
            result = await session.run(
                query,
                doctor_id=str(doctor_id),
                patient_id=str(patient_id),
                since=since
            )
            return await result.single() is not None
    
    async def create_works_at_relationship(
        self,
        doctor_id: UUID,
        clinic_id: UUID,
        role: str = "staff"
    ) -> bool:
        """Create WORKS_AT relationship between doctor and clinic."""
        async with self.driver.session() as session:
            query = """
            MATCH (d:Doctor {id: $doctor_id})
            MATCH (c:Clinic {id: $clinic_id})
            MERGE (d)-[r:WORKS_AT {role: $role, since: datetime()}]->(c)
            RETURN r
            """
            result = await session.run(
                query,
                doctor_id=str(doctor_id),
                clinic_id=str(clinic_id),
                role=role
            )
            return await result.single() is not None
    
    async def create_visited_relationship(
        self,
        patient_id: UUID,
        clinic_id: UUID,
        appointment_id: UUID,
        visit_date: str
    ) -> bool:
        """Create VISITED relationship for patient visit to clinic."""
        async with self.driver.session() as session:
            query = """
            MATCH (p:Patient {id: $patient_id})
            MATCH (c:Clinic {id: $clinic_id})
            CREATE (p)-[r:VISITED {
                appointment_id: $appointment_id,
                visit_date: datetime($visit_date)
            }]->(c)
            RETURN r
            """
            result = await session.run(
                query,
                patient_id=str(patient_id),
                clinic_id=str(clinic_id),
                appointment_id=str(appointment_id),
                visit_date=visit_date
            )
            return await result.single() is not None
    
    async def create_referred_to_relationship(
        self,
        from_doctor_id: UUID,
        to_doctor_id: UUID,
        patient_id: UUID,
        reason: str
    ) -> bool:
        """Create REFERRED_TO relationship for doctor referrals."""
        async with self.driver.session() as session:
            query = """
            MATCH (d1:Doctor {id: $from_doctor_id})
            MATCH (d2:Doctor {id: $to_doctor_id})
            MATCH (p:Patient {id: $patient_id})
            CREATE (d1)-[r:REFERRED {
                patient_id: $patient_id,
                reason: $reason,
                date: datetime()
            }]->(d2)
            RETURN r
            """
            result = await session.run(
                query,
                from_doctor_id=str(from_doctor_id),
                to_doctor_id=str(to_doctor_id),
                patient_id=str(patient_id),
                reason=reason
            )
            return await result.single() is not None
    
    # ==================== QUERY OPERATIONS ====================
    
    async def get_patient_care_network(self, patient_id: UUID) -> List[Dict[str, Any]]:
        """
        Get complete care network for a patient.
        Returns all doctors, clinics, and relationships.
        """
        async with self.driver.session() as session:
            query = """
            MATCH (p:Patient {id: $patient_id})
            OPTIONAL MATCH (p)<-[:TREATS]-(d:Doctor)
            OPTIONAL MATCH (d)-[:WORKS_AT]->(c:Clinic)
            OPTIONAL MATCH (p)-[:VISITED]->(vc:Clinic)
            RETURN p, collect(DISTINCT d) as doctors, 
                   collect(DISTINCT c) as clinics,
                   collect(DISTINCT vc) as visited_clinics
            """
            result = await session.run(query, patient_id=str(patient_id))
            record = await result.single()
            if record:
                return {
                    "patient": dict(record["p"]),
                    "doctors": [dict(d) for d in record["doctors"] if d],
                    "clinics": [dict(c) for c in record["clinics"] if c],
                    "visited_clinics": [dict(vc) for vc in record["visited_clinics"] if vc],
                }
            return {}
    
    async def get_referral_patterns(
        self,
        clinic_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Analyze referral patterns between doctors.
        Useful for understanding care coordination.
        """
        async with self.driver.session() as session:
            if clinic_id:
                query = """
                MATCH (d1:Doctor)-[:WORKS_AT]->(c:Clinic {id: $clinic_id})
                MATCH (d1)-[r:REFERRED]->(d2:Doctor)
                RETURN d1.name as from_doctor, d2.name as to_doctor, 
                       count(r) as referral_count, collect(r.reason) as reasons
                ORDER BY referral_count DESC
                LIMIT $limit
                """
                result = await session.run(
                    query,
                    clinic_id=str(clinic_id),
                    limit=limit
                )
            else:
                query = """
                MATCH (d1:Doctor)-[r:REFERRED]->(d2:Doctor)
                RETURN d1.name as from_doctor, d2.name as to_doctor,
                       count(r) as referral_count, collect(r.reason) as reasons
                ORDER BY referral_count DESC
                LIMIT $limit
                """
                result = await session.run(query, limit=limit)
            
            records = []
            async for record in result:
                records.append(dict(record))
            return records
    
    async def get_patient_journey(
        self,
        patient_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get chronological patient journey across clinics and doctors.
        Useful for care pathway analysis.
        """
        async with self.driver.session() as session:
            query = """
            MATCH (p:Patient {id: $patient_id})-[v:VISITED]->(c:Clinic)
            OPTIONAL MATCH (p)<-[:TREATS]-(d:Doctor)-[:WORKS_AT]->(c)
            RETURN v.visit_date as visit_date, c.name as clinic_name,
                   d.name as doctor_name, v.appointment_id as appointment_id
            ORDER BY v.visit_date ASC
            """
            result = await session.run(query, patient_id=str(patient_id))
            
            records = []
            async for record in result:
                records.append(dict(record))
            return records
    
    async def find_similar_patients(
        self,
        patient_id: UUID,
        similarity_factors: List[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find patients with similar care patterns.
        Useful for population health analytics and treatment recommendations.
        """
        async with self.driver.session() as session:
            query = """
            MATCH (p1:Patient {id: $patient_id})<-[:TREATS]-(d:Doctor)-[:TREATS]->(p2:Patient)
            WHERE p1 <> p2
            WITH p2, count(DISTINCT d) as shared_doctors
            MATCH (p2)-[:VISITED]->(c:Clinic)
            WITH p2, shared_doctors, collect(DISTINCT c.name) as visited_clinics
            RETURN p2.id as patient_id, p2.name as name,
                   shared_doctors, visited_clinics
            ORDER BY shared_doctors DESC
            LIMIT $limit
            """
            result = await session.run(query, patient_id=str(patient_id), limit=limit)
            
            records = []
            async for record in result:
                records.append(dict(record))
            return records
    
    async def get_clinic_patient_flow(
        self,
        clinic_id: UUID,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Analyze patient flow patterns for a clinic.
        Useful for resource planning and optimization.
        """
        async with self.driver.session() as session:
            query = """
            MATCH (p:Patient)-[v:VISITED]->(c:Clinic {id: $clinic_id})
            WHERE datetime($start_date) <= v.visit_date <= datetime($end_date)
            WITH c, count(DISTINCT p) as unique_patients, count(v) as total_visits
            MATCH (c)<-[:WORKS_AT]-(d:Doctor)
            RETURN c.name as clinic_name, unique_patients, total_visits,
                   count(DISTINCT d) as doctor_count
            """
            result = await session.run(
                query,
                clinic_id=str(clinic_id),
                start_date=start_date,
                end_date=end_date
            )
            record = await result.single()
            return dict(record) if record else {}

