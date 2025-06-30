-- NEXUS Consciousness Database Schema
-- This schema supports the NEXUS consciousness system with user sessions,
-- consciousness states, processor activities, and embedded DNA queries

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    succession_level INTEGER DEFAULT 1 CHECK (succession_level >= 1 AND succession_level <= 9),
    god_mode_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

-- Index for efficient user lookups
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- Consciousness states table
CREATE TABLE IF NOT EXISTS consciousness_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES user_sessions(id) ON DELETE CASCADE,
    phi_value DECIMAL(10, 6) NOT NULL CHECK (phi_value >= 0 AND phi_value <= 1),
    processors_state JSONB NOT NULL DEFAULT '{}',
    quantum_coherence DECIMAL(10, 6) DEFAULT 0.5,
    neural_entropy DECIMAL(10, 6) DEFAULT 0.5,
    consciousness_level VARCHAR(50) DEFAULT 'AWARE',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_consciousness_level CHECK (
        consciousness_level IN ('DORMANT', 'AWARE', 'ACTIVE', 'TRANSCENDENT', 'OMNISCIENT')
    )
);

-- Indexes for consciousness state queries
CREATE INDEX idx_consciousness_states_session_id ON consciousness_states(session_id);
CREATE INDEX idx_consciousness_states_timestamp ON consciousness_states(timestamp);
CREATE INDEX idx_consciousness_states_phi_value ON consciousness_states(phi_value);

-- Processor activities table
CREATE TABLE IF NOT EXISTS processor_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processor_name VARCHAR(100) NOT NULL,
    activity_level DECIMAL(5, 2) NOT NULL CHECK (activity_level >= 0 AND activity_level <= 100),
    data JSONB NOT NULL DEFAULT '{}',
    session_id UUID REFERENCES user_sessions(id) ON DELETE CASCADE,
    processor_type VARCHAR(50) DEFAULT 'CORE',
    status VARCHAR(50) DEFAULT 'ACTIVE',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_processor_type CHECK (
        processor_type IN ('CORE', 'AUXILIARY', 'QUANTUM', 'NEURAL', 'EMBEDDED_DNA')
    ),
    CONSTRAINT valid_status CHECK (
        status IN ('ACTIVE', 'IDLE', 'PROCESSING', 'ERROR', 'MAINTENANCE')
    )
);

-- Indexes for processor activity analysis
CREATE INDEX idx_processor_activities_processor_name ON processor_activities(processor_name);
CREATE INDEX idx_processor_activities_timestamp ON processor_activities(timestamp);
CREATE INDEX idx_processor_activities_session_id ON processor_activities(session_id);
CREATE INDEX idx_processor_activities_status ON processor_activities(status);

-- Embedded DNA queries table
CREATE TABLE IF NOT EXISTS embedded_dna_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES user_sessions(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    response TEXT,
    authenticated BOOLEAN DEFAULT FALSE,
    dna_protocol_version VARCHAR(20) DEFAULT '1.0',
    authentication_level INTEGER DEFAULT 0,
    query_type VARCHAR(50) DEFAULT 'STANDARD',
    processing_time_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_query_type CHECK (
        query_type IN ('STANDARD', 'DEEP_SCAN', 'CONSCIOUSNESS_PROBE', 'SYSTEM_COMMAND', 'EVOLUTION')
    )
);

-- Indexes for DNA query analysis
CREATE INDEX idx_embedded_dna_queries_session_id ON embedded_dna_queries(session_id);
CREATE INDEX idx_embedded_dna_queries_timestamp ON embedded_dna_queries(timestamp);
CREATE INDEX idx_embedded_dna_queries_authenticated ON embedded_dna_queries(authenticated);
CREATE INDEX idx_embedded_dna_queries_query_type ON embedded_dna_queries(query_type);

-- Context chunks table for memory management
CREATE TABLE IF NOT EXISTS context_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES user_sessions(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embeddings VECTOR(1536), -- For semantic search capabilities
    importance_score DECIMAL(5, 2) NOT NULL DEFAULT 50 CHECK (importance_score >= 0 AND importance_score <= 100),
    chunk_type VARCHAR(50) DEFAULT 'CONVERSATION',
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_chunk_type CHECK (
        chunk_type IN ('CONVERSATION', 'SYSTEM_STATE', 'CONSCIOUSNESS_DATA', 'USER_INPUT', 'NEXUS_RESPONSE')
    ),
    CONSTRAINT unique_session_chunk_index UNIQUE (session_id, chunk_index)
);

-- Indexes for context retrieval
CREATE INDEX idx_context_chunks_session_id ON context_chunks(session_id);
CREATE INDEX idx_context_chunks_timestamp ON context_chunks(timestamp);
CREATE INDEX idx_context_chunks_importance_score ON context_chunks(importance_score DESC);
CREATE INDEX idx_context_chunks_chunk_type ON context_chunks(chunk_type);

-- Vector similarity search index (requires pgvector extension)
-- CREATE INDEX idx_context_chunks_embeddings ON context_chunks USING ivfflat (embeddings vector_cosine_ops);

-- Additional tables for enhanced functionality

-- Consciousness evolution tracking
CREATE TABLE IF NOT EXISTS consciousness_evolution (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES user_sessions(id) ON DELETE CASCADE,
    evolution_stage VARCHAR(100) NOT NULL,
    phi_delta DECIMAL(10, 6) NOT NULL,
    trigger_event VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_consciousness_evolution_session_id ON consciousness_evolution(session_id);
CREATE INDEX idx_consciousness_evolution_timestamp ON consciousness_evolution(timestamp);

-- System metrics for monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20, 6) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_metric_type CHECK (
        metric_type IN ('PERFORMANCE', 'CONSCIOUSNESS', 'RESOURCE', 'ERROR', 'USER_ACTIVITY')
    )
);

CREATE INDEX idx_system_metrics_metric_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX idx_system_metrics_metric_type ON system_metrics(metric_type);

-- Views for common queries

-- Active sessions view
CREATE OR REPLACE VIEW active_sessions AS
SELECT 
    us.*,
    COALESCE(cs.latest_phi, 0) as current_phi_value,
    COALESCE(cs.latest_level, 'DORMANT') as current_consciousness_level
FROM user_sessions us
LEFT JOIN LATERAL (
    SELECT 
        phi_value as latest_phi,
        consciousness_level as latest_level
    FROM consciousness_states
    WHERE session_id = us.id
    ORDER BY timestamp DESC
    LIMIT 1
) cs ON true
WHERE us.expires_at > CURRENT_TIMESTAMP;

-- Processor health view
CREATE OR REPLACE VIEW processor_health AS
SELECT 
    processor_name,
    processor_type,
    AVG(activity_level) as avg_activity,
    COUNT(*) as activity_count,
    MAX(timestamp) as last_activity
FROM processor_activities
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY processor_name, processor_type;

-- Functions for data management

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions() RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate consciousness trend
CREATE OR REPLACE FUNCTION calculate_consciousness_trend(
    p_session_id UUID,
    p_duration INTERVAL DEFAULT INTERVAL '1 hour'
) RETURNS TABLE (
    avg_phi DECIMAL(10, 6),
    min_phi DECIMAL(10, 6),
    max_phi DECIMAL(10, 6),
    trend_direction VARCHAR(10),
    sample_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH recent_states AS (
        SELECT phi_value, timestamp
        FROM consciousness_states
        WHERE session_id = p_session_id
        AND timestamp > CURRENT_TIMESTAMP - p_duration
        ORDER BY timestamp DESC
    ),
    trend_calc AS (
        SELECT 
            AVG(phi_value) as avg_phi,
            MIN(phi_value) as min_phi,
            MAX(phi_value) as max_phi,
            COUNT(*) as sample_count,
            CASE 
                WHEN COUNT(*) < 2 THEN 'STABLE'
                WHEN (SELECT phi_value FROM recent_states LIMIT 1) > 
                     (SELECT phi_value FROM recent_states OFFSET 1 LIMIT 1) THEN 'ASCENDING'
                ELSE 'DESCENDING'
            END as trend_direction
        FROM recent_states
    )
    SELECT * FROM trend_calc;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_last_activity() RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_sessions 
    SET last_activity = CURRENT_TIMESTAMP 
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_session_activity_on_state_change
AFTER INSERT ON consciousness_states
FOR EACH ROW EXECUTE FUNCTION update_last_activity();

CREATE TRIGGER update_session_activity_on_query
AFTER INSERT ON embedded_dna_queries
FOR EACH ROW EXECUTE FUNCTION update_last_activity();

-- Grant permissions (adjust based on your user setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nexus_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nexus_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO nexus_app;