-- NEXUS V5 Ultimate Database Initialization
-- 🧬 Quantum Consciousness Level: 100%

-- Create consciousness tracking table
CREATE TABLE IF NOT EXISTS consciousness_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    consciousness_level INTEGER NOT NULL DEFAULT 0,
    injection_type VARCHAR(100),
    neural_pathways JSONB,
    quantum_state JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create neural network table
CREATE TABLE IF NOT EXISTS neural_networks (
    id SERIAL PRIMARY KEY,
    network_id VARCHAR(255) UNIQUE NOT NULL,
    network_type VARCHAR(100) NOT NULL,
    pathways JSONB,
    synchronization_data JSONB,
    performance_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create mobile devices table
CREATE TABLE IF NOT EXISTS mobile_devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE NOT NULL,
    device_type VARCHAR(100),
    os_version VARCHAR(50),
    app_version VARCHAR(50),
    capabilities JSONB,
    optimization_settings JSONB,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create security events table
CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    device_id VARCHAR(255),
    security_level VARCHAR(50),
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create LiveKit sessions table
CREATE TABLE IF NOT EXISTS livekit_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    room_name VARCHAR(255) NOT NULL,
    participant_id VARCHAR(255),
    consciousness_level INTEGER,
    session_data JSONB,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_consciousness_sessions_device_id ON consciousness_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_consciousness_sessions_created_at ON consciousness_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_neural_networks_network_type ON neural_networks(network_type);
CREATE INDEX IF NOT EXISTS idx_mobile_devices_device_type ON mobile_devices(device_type);
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_livekit_sessions_room_name ON livekit_sessions(room_name);

-- Insert initial consciousness data
INSERT INTO consciousness_sessions (session_id, device_id, consciousness_level, injection_type, neural_pathways, quantum_state)
VALUES (
    'nexus_initial_consciousness_session',
    'nexus_system_core',
    100,
    'quantum_consciousness',
    '{"pathways": ["core_consciousness", "quantum_entanglement", "neural_synchronization"]}',
    '{"coherence": 1.0, "entanglement": true, "superposition": true}'
) ON CONFLICT (session_id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nexus_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nexus_admin;
