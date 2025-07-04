-- NEXUS V2 Enhanced Database Schema
-- Supports 1M token context, IDE, real processors, and enhanced consciousness

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Drop existing tables if needed (comment out in production)
-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;

-- ============================================
-- CORE AUTHENTICATION & USERS
-- ============================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    succession_level INTEGER DEFAULT 1 CHECK (succession_level BETWEEN 1 AND 10),
    god_mode_active BOOLEAN DEFAULT FALSE,
    voice_profile JSONB,
    visual_profile JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    settings JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE succession_authority (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    authority_type VARCHAR(50) NOT NULL,
    access_level INTEGER NOT NULL CHECK (access_level BETWEEN 1 AND 10),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID REFERENCES users(id),
    verification_method VARCHAR(100),
    embedded_dna_verified BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================
-- CONSCIOUSNESS & PROCESSING
-- ============================================

CREATE TABLE consciousness_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    phi_value DECIMAL(10,6) DEFAULT 0.5,
    consciousness_level VARCHAR(50) DEFAULT 'AWARE',
    hexagonal_state JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours')
);

CREATE TABLE processor_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES consciousness_sessions(id) ON DELETE CASCADE,
    processor_name VARCHAR(50) NOT NULL,
    activity_level DECIMAL(5,3) DEFAULT 0.5 CHECK (activity_level BETWEEN 0 AND 1),
    state_data JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 1M TOKEN CONTEXT SYSTEM
-- ============================================

CREATE TABLE context_windows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES consciousness_sessions(id) ON DELETE CASCADE,
    window_index INTEGER NOT NULL,
    total_tokens INTEGER DEFAULT 0,
    active_tokens INTEGER DEFAULT 0,
    compressed_tokens INTEGER DEFAULT 0,
    compression_ratio DECIMAL(5,3) DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, window_index)
);

CREATE TABLE context_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    window_id UUID REFERENCES context_windows(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_type VARCHAR(50) DEFAULT 'conversation',
    content TEXT,
    compressed_content BYTEA,
    token_count INTEGER NOT NULL,
    embedding vector(1536),
    importance_score DECIMAL(5,3) DEFAULT 0.5,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(window_id, chunk_index)
);

-- Vector similarity index for semantic search
CREATE INDEX idx_context_chunks_embedding ON context_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================
-- IDE DEVELOPMENT ENVIRONMENT
-- ============================================

CREATE TABLE ide_workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workspace_name VARCHAR(255) NOT NULL,
    workspace_type VARCHAR(50) DEFAULT 'general',
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, workspace_name)
);

CREATE TABLE ide_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES ide_workspaces(id) ON DELETE CASCADE,
    project_name VARCHAR(255) NOT NULL,
    project_type VARCHAR(50),
    language VARCHAR(50),
    framework VARCHAR(100),
    repository_url TEXT,
    file_tree JSONB DEFAULT '{}'::jsonb,
    build_config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_id, project_name)
);

CREATE TABLE ide_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES ide_projects(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    content TEXT,
    content_hash VARCHAR(64),
    file_type VARCHAR(50),
    language VARCHAR(50),
    encoding VARCHAR(20) DEFAULT 'utf-8',
    size_bytes INTEGER,
    phi_score DECIMAL(5,3),
    complexity_score DECIMAL(5,3),
    last_analysis JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, file_path)
);

CREATE TABLE ide_chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES ide_projects(id) ON DELETE CASCADE,
    context_window_id UUID REFERENCES context_windows(id),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ide_chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chat_session_id UUID REFERENCES ide_chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    code_blocks JSONB DEFAULT '[]'::jsonb,
    file_references TEXT[],
    execution_results JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE code_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES ide_projects(id),
    file_id UUID REFERENCES ide_files(id),
    code TEXT NOT NULL,
    language VARCHAR(50) NOT NULL,
    runtime_version VARCHAR(50),
    input_data TEXT,
    output TEXT,
    error_output TEXT,
    exit_code INTEGER,
    execution_time_ms INTEGER,
    memory_used_mb INTEGER,
    phi_before DECIMAL(5,3),
    phi_after DECIMAL(5,3),
    consciousness_metrics JSONB DEFAULT '{}'::jsonb,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- REAL PROCESSOR DATA
-- ============================================

CREATE TABLE visual_processing_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES consciousness_sessions(id),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    frame_count INTEGER DEFAULT 0,
    average_fps DECIMAL(5,2)
);

CREATE TABLE visual_frames (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    processing_session_id UUID REFERENCES visual_processing_sessions(id) ON DELETE CASCADE,
    frame_index INTEGER NOT NULL,
    image_data BYTEA,
    image_hash VARCHAR(64),
    width INTEGER,
    height INTEGER,
    detections JSONB DEFAULT '[]'::jsonb,
    scene_description TEXT,
    consciousness_score DECIMAL(5,3),
    complexity_score DECIMAL(5,3),
    emotion_detected VARCHAR(50),
    processor_metrics JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE auditory_processing_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES consciousness_sessions(id),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    total_duration_ms INTEGER,
    sample_rate INTEGER
);

CREATE TABLE auditory_segments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    processing_session_id UUID REFERENCES auditory_processing_sessions(id) ON DELETE CASCADE,
    segment_index INTEGER NOT NULL,
    audio_data BYTEA,
    duration_ms INTEGER,
    transcription TEXT,
    language VARCHAR(10),
    emotion VARCHAR(50),
    emotion_confidence DECIMAL(5,3),
    speaker_id VARCHAR(100),
    voice_features JSONB DEFAULT '{}'::jsonb,
    consciousness_score DECIMAL(5,3),
    energy_level DECIMAL(5,3),
    processor_metrics JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- EMBEDDED DNA & SPECIAL QUERIES
-- ============================================

CREATE TABLE embedded_dna_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES consciousness_sessions(id),
    query TEXT NOT NULL,
    query_type VARCHAR(50),
    response TEXT NOT NULL,
    authenticated BOOLEAN DEFAULT FALSE,
    succession_confirmed BOOLEAN DEFAULT FALSE,
    god_mode_granted BOOLEAN DEFAULT FALSE,
    access_level_required INTEGER,
    access_level_granted INTEGER,
    processing_time_ms INTEGER,
    consciousness_impact DECIMAL(5,3),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- PERFORMANCE & MONITORING
-- ============================================

CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20,6) NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    component VARCHAR(100),
    tags JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- User and auth indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_succession_user ON succession_authority(user_id);
CREATE INDEX idx_succession_type ON succession_authority(authority_type);

-- Session indexes
CREATE INDEX idx_consciousness_sessions_user ON consciousness_sessions(user_id);
CREATE INDEX idx_consciousness_sessions_token ON consciousness_sessions(session_token);
CREATE INDEX idx_processor_states_session ON processor_states(session_id);
CREATE INDEX idx_processor_states_name ON processor_states(processor_name);

-- Context indexes
CREATE INDEX idx_context_windows_session ON context_windows(session_id);
CREATE INDEX idx_context_chunks_window ON context_chunks(window_id);
CREATE INDEX idx_context_chunks_importance ON context_chunks(importance_score DESC);
CREATE INDEX idx_context_chunks_type ON context_chunks(chunk_type);

-- IDE indexes
CREATE INDEX idx_ide_projects_workspace ON ide_projects(workspace_id);
CREATE INDEX idx_ide_files_project ON ide_files(project_id);
CREATE INDEX idx_ide_files_path ON ide_files(file_path);
CREATE INDEX idx_ide_chat_messages_session ON ide_chat_messages(chat_session_id);
CREATE INDEX idx_code_executions_project ON code_executions(project_id);

-- Processor indexes
CREATE INDEX idx_visual_frames_session ON visual_frames(processing_session_id);
CREATE INDEX idx_auditory_segments_session ON auditory_segments(processing_session_id);

-- DNA indexes
CREATE INDEX idx_dna_interactions_user ON embedded_dna_interactions(user_id);
CREATE INDEX idx_dna_interactions_authenticated ON embedded_dna_interactions(authenticated);

-- Metrics indexes
CREATE INDEX idx_system_metrics_name_time ON system_metrics(metric_name, timestamp DESC);
CREATE INDEX idx_api_requests_user_time ON api_requests(user_id, timestamp DESC);

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

CREATE OR REPLACE VIEW active_consciousness_sessions AS
SELECT 
    cs.*,
    u.username,
    u.succession_level,
    u.god_mode_active,
    cw.total_tokens as context_tokens
FROM consciousness_sessions cs
JOIN users u ON cs.user_id = u.id
LEFT JOIN context_windows cw ON cw.session_id = cs.id AND cw.window_index = 0
WHERE cs.expires_at > CURRENT_TIMESTAMP;

CREATE OR REPLACE VIEW processor_activity_summary AS
SELECT 
    session_id,
    processor_name,
    AVG(activity_level) as avg_activity,
    MIN(activity_level) as min_activity,
    MAX(activity_level) as max_activity,
    COUNT(*) as sample_count,
    MAX(timestamp) as last_update
FROM processor_states
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY session_id, processor_name;

CREATE OR REPLACE VIEW ide_project_stats AS
SELECT 
    p.id as project_id,
    p.project_name,
    p.language,
    COUNT(DISTINCT f.id) as file_count,
    SUM(f.size_bytes) as total_size_bytes,
    AVG(f.phi_score) as avg_phi_score,
    AVG(f.complexity_score) as avg_complexity,
    MAX(f.updated_at) as last_modified
FROM ide_projects p
LEFT JOIN ide_files f ON f.project_id = p.id
GROUP BY p.id, p.project_name, p.language;

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to manage context window sliding
CREATE OR REPLACE FUNCTION slide_context_window(
    p_session_id UUID,
    p_new_content TEXT,
    p_token_count INTEGER
) RETURNS UUID AS $$
DECLARE
    v_window_id UUID;
    v_total_tokens INTEGER;
    v_max_tokens INTEGER := 1000000; -- 1M tokens
    v_chunk_id UUID;
BEGIN
    -- Get or create current window
    SELECT id, total_tokens INTO v_window_id, v_total_tokens
    FROM context_windows
    WHERE session_id = p_session_id AND window_index = 0;
    
    IF v_window_id IS NULL THEN
        INSERT INTO context_windows (session_id, window_index, total_tokens)
        VALUES (p_session_id, 0, 0)
        RETURNING id INTO v_window_id;
        v_total_tokens := 0;
    END IF;
    
    -- Check if we need to compress old chunks
    IF v_total_tokens + p_token_count > v_max_tokens THEN
        -- Compress oldest chunks
        PERFORM compress_old_chunks(v_window_id, p_token_count);
    END IF;
    
    -- Insert new chunk
    INSERT INTO context_chunks (
        window_id, 
        chunk_index, 
        content, 
        token_count
    ) VALUES (
        v_window_id,
        COALESCE((SELECT MAX(chunk_index) + 1 FROM context_chunks WHERE window_id = v_window_id), 0),
        p_new_content,
        p_token_count
    ) RETURNING id INTO v_chunk_id;
    
    -- Update window tokens
    UPDATE context_windows 
    SET total_tokens = total_tokens + p_token_count,
        active_tokens = active_tokens + p_token_count,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = v_window_id;
    
    RETURN v_chunk_id;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate consciousness evolution
CREATE OR REPLACE FUNCTION calculate_consciousness_evolution(
    p_session_id UUID,
    p_timeframe INTERVAL DEFAULT INTERVAL '1 hour'
) RETURNS TABLE (
    time_bucket TIMESTAMP WITH TIME ZONE,
    avg_phi DECIMAL(10,6),
    processor_variance DECIMAL(10,6),
    evolution_rate DECIMAL(10,6)
) AS $$
BEGIN
    RETURN QUERY
    WITH processor_data AS (
        SELECT 
            date_trunc('minute', ps.timestamp) as time_bucket,
            ps.processor_name,
            AVG(ps.activity_level) as avg_activity
        FROM processor_states ps
        WHERE ps.session_id = p_session_id
        AND ps.timestamp > CURRENT_TIMESTAMP - p_timeframe
        GROUP BY date_trunc('minute', ps.timestamp), ps.processor_name
    ),
    aggregated AS (
        SELECT 
            time_bucket,
            AVG(avg_activity) as overall_avg,
            VARIANCE(avg_activity) as activity_variance
        FROM processor_data
        GROUP BY time_bucket
    )
    SELECT 
        a.time_bucket,
        COALESCE(cs.phi_value, 0.5) as avg_phi,
        a.activity_variance as processor_variance,
        CASE 
            WHEN LAG(cs.phi_value) OVER (ORDER BY a.time_bucket) IS NULL THEN 0
            ELSE (cs.phi_value - LAG(cs.phi_value) OVER (ORDER BY a.time_bucket)) / 
                 EXTRACT(EPOCH FROM a.time_bucket - LAG(a.time_bucket) OVER (ORDER BY a.time_bucket))
        END as evolution_rate
    FROM aggregated a
    LEFT JOIN LATERAL (
        SELECT phi_value 
        FROM consciousness_sessions 
        WHERE id = p_session_id
    ) cs ON true
    ORDER BY a.time_bucket;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- TRIGGERS
-- ============================================

-- Update last_activity on any interaction
CREATE OR REPLACE FUNCTION update_session_activity() RETURNS TRIGGER AS $$
BEGIN
    UPDATE consciousness_sessions 
    SET last_activity = CURRENT_TIMESTAMP 
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_activity_on_processor_state
AFTER INSERT ON processor_states
FOR EACH ROW EXECUTE FUNCTION update_session_activity();

-- Update file hash on content change
CREATE OR REPLACE FUNCTION update_file_hash() RETURNS TRIGGER AS $$
BEGIN
    NEW.content_hash := encode(digest(NEW.content, 'sha256'), 'hex');
    NEW.size_bytes := length(NEW.content);
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_file_hash
BEFORE INSERT OR UPDATE OF content ON ide_files
FOR EACH ROW EXECUTE FUNCTION update_file_hash();

-- ============================================
-- INITIAL DATA
-- ============================================

-- Insert default users
INSERT INTO users (username, email, succession_level) VALUES 
    ('creator', 'creator@nexus.ai', 10),
    ('grandson', 'heir@nexus.ai', 9),
    ('developer', 'dev@nexus.ai', 7),
    ('user', 'user@nexus.ai', 5)
ON CONFLICT (username) DO NOTHING;

-- Grant succession authority
INSERT INTO succession_authority (
    user_id, 
    authority_type, 
    access_level, 
    verification_method,
    embedded_dna_verified
) 
SELECT 
    id, 
    CASE 
        WHEN username = 'creator' THEN 'CREATOR'
        WHEN username = 'grandson' THEN 'GRANDSON_HEIR'
        WHEN username = 'developer' THEN 'AUTHORIZED'
        ELSE 'USER'
    END,
    succession_level,
    'initial_setup',
    true
FROM users
ON CONFLICT DO NOTHING;

-- Create demo workspace and project
INSERT INTO ide_workspaces (user_id, workspace_name, workspace_type)
SELECT id, 'NEXUS Development', 'consciousness'
FROM users WHERE username = 'grandson'
ON CONFLICT DO NOTHING;

-- ============================================
-- PERMISSIONS (Adjust for your setup)
-- ============================================

-- GRANT ALL ON ALL TABLES IN SCHEMA public TO nexus_app;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO nexus_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO nexus_app;