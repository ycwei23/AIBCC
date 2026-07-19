-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Projects
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    building_use TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Files
CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    format TEXT NOT NULL CHECK (format IN ('pdf', 'png', 'ifc', 'dxf')),
    hash TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    pages INTEGER,
    parse_status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rules
CREATE TABLE IF NOT EXISTS rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id TEXT UNIQUE NOT NULL,
    law_name TEXT NOT NULL,
    article TEXT,
    version TEXT NOT NULL,
    scope JSONB,
    target TEXT,
    operator TEXT,
    threshold FLOAT,
    unit TEXT,
    severity TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('draft', 'active', 'deprecated')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analysis Runs
-- Status state machine: uploaded → document_parsing → vlm_extracting → geometry_validating
--   → graph_building → rule_checking → agent_explaining → completed | review_required | failed
CREATE TABLE IF NOT EXISTS analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_id UUID REFERENCES files(id),
    status TEXT NOT NULL DEFAULT 'uploaded',
    parser_version TEXT,
    vlm_version TEXT,
    rule_version TEXT,
    duration_seconds FLOAT,
    cost_usd FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Building Elements
CREATE TABLE IF NOT EXISTS building_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    element_id TEXT NOT NULL,
    type TEXT NOT NULL,
    page INTEGER,
    bbox JSONB,
    geometry JSONB,
    source TEXT,
    confidence FLOAT,
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Graph Nodes (Building → Floor → Space → Element → Path → Exit → Rule)
CREATE TABLE IF NOT EXISTS graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    node_id TEXT NOT NULL,
    node_type TEXT NOT NULL CHECK (node_type IN ('Building', 'Floor', 'Space', 'Element', 'Path', 'Exit', 'Rule')),
    properties JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Graph Edges (semantic relations between nodes)
CREATE TABLE IF NOT EXISTS graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    from_node TEXT NOT NULL,
    relation TEXT NOT NULL,
    to_node TEXT NOT NULL,
    source TEXT,
    confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Runs (one per /copilot question)
CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    question TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    answer TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Steps (tool calls within an agent run)
CREATE TABLE IF NOT EXISTS agent_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    tool_name TEXT,
    tool_input JSONB,
    tool_output JSONB,
    evidence_ids JSONB,
    citations JSONB,
    confidence FLOAT,
    model_version TEXT,
    rule_version TEXT,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Violations
CREATE TABLE IF NOT EXISTS violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    violation_id TEXT NOT NULL,
    rule_id TEXT REFERENCES rules(rule_id),
    element_ids JSONB,
    graph_path JSONB,
    measured FLOAT,
    required FLOAT,
    status TEXT CHECK (status IN ('fail', 'warning', 'pass', 'not_applicable', 'insufficient_data')),
    page INTEGER,
    highlight JSONB,
    evidence TEXT,
    suggestion TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reports
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    file_path TEXT,
    summary TEXT,
    trace_id TEXT
);

-- Indexes for common access patterns
CREATE INDEX IF NOT EXISTS idx_files_project_id ON files(project_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_project_id ON analysis_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_building_elements_run_id ON building_elements(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_run_id ON graph_nodes(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_run_id ON graph_edges(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_violations_run_id ON violations(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_analysis_run_id ON agent_runs(analysis_run_id);
CREATE INDEX IF NOT EXISTS idx_agent_steps_agent_run_id ON agent_steps(agent_run_id);
