const BACKEND_URL = 'http://127.0.0.1:8000';


export interface ClassResponse {
  id: string;
  name: string;
  type: string;
  modifiers: string[];
  annotations: string[];
  extends: string | null;
  implements: string[];
}

export interface MethodResponse {
  id: string;
  name: string;
  modifiers: string[];
  annotations: string[];
  is_constructor: boolean;
  parameter_names: string[];
  parameter_types: string[];
  return_type: string | null;
}

export interface FieldResponse {
  id: string;
  name: string;
  type: string;
  modifiers: string[];
  annotations: string[];
  initializer: string | null;
}

export interface ClassHistoryResponse {
  class_id: string;
  history: {
    hash: string;
    message: string;
    author: string;
    email: string;
    timestamp: string;
    file_path: string;
  }[];
}

export interface DependencyGroupResponse {
  imports: ClassResponse[];
  extends: ClassResponse[];
  implements: ClassResponse[];
}

export interface ChangeCouplingItem {
  file1: string;
  file2: string;
  count: number;
  confidence: number;
}

export interface ChangeCouplingResponse {
  status: string;
  count: number;
  data: ChangeCouplingItem[];
}

// ---------------------------------------------------------------------------
// 1. Health & Ingestion
// ---------------------------------------------------------------------------
export async function checkBackendHealth(): Promise<{ status: string; neo4j: boolean }> {
  try {
    const res = await fetch(`${BACKEND_URL}/health`);
    if (!res.ok) return { status: 'offline', neo4j: false };
    const data = await res.json();
    return {
      status: data.status,
      neo4j: data.neo4j === 'connected' || data.status === 'healthy',
    };
  } catch (error) {
    return { status: 'offline', neo4j: false };
  }
}

function normalizeRepositoryUrl(repoUrl: string): string {
  const trimmed = repoUrl.trim();
  if (/^[a-zA-Z][a-zA-Z\d+\-.]*:\/\//.test(trimmed)) {
    return trimmed;
  }
  return `https://${trimmed}`;
}

export async function connectBackendRepository(repoUrl: string) {
  try {
    const normalizedUrl = normalizeRepositoryUrl(repoUrl);
    const response = await fetch(`${BACKEND_URL}/repositories/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: normalizedUrl }),
    });
    if (!response.ok) throw new Error(`Connect error: ${response.statusText}`);
    return await response.json();
  } catch (error) {
    console.error('Error connecting repo:', error);
    return null;
  }
}

// ---------------------------------------------------------------------------
// 2. Index Repository (POST /repositories/index)
// ---------------------------------------------------------------------------
export async function indexBackendRepository(repoUrl: string): Promise<{ status: string; repository: string } | null> {
  try {
    const normalizedUrl = normalizeRepositoryUrl(repoUrl);
    const indexResponse = await fetch(`${BACKEND_URL}/repositories/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repository_url: normalizedUrl }),
    });

    if (!indexResponse.ok) {
      const errorText = await indexResponse.text();
      console.error('Repository indexing failed:', errorText);
      throw new Error(`Indexing failed: ${indexResponse.status} - ${errorText}`);
    }

    const data = await indexResponse.json();
    return data;
  } catch (error) {
    if (error instanceof TypeError) {
      console.error('Backend network failure:', error);
      return null;
    }

    console.error('Failed to index repository:', error);
    throw error;
  }
}

// ---------------------------------------------------------------------------
// 3. Try to Find Main Class (workaround for missing list endpoint)
// ---------------------------------------------------------------------------
export async function tryFindMainClass(repoName: string): Promise<string | null> {
  console.log(`🔍 Searching for main class in repository: ${repoName}`);
  
  // Remove hyphens and convert to PascalCase for common Spring Boot naming
  const cleanRepoName = repoName
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join('');
  
  // Common patterns for Spring Boot and general Java main classes
  const commonMainClassNames = [
    'Application',
    'Main',
    'App',
    `${cleanRepoName}Application`,
    `${repoName}Application`, // Try with original name too
    `${cleanRepoName}Main`,
    'SpringApplication',
    'DemoApplication',
    'BlogPlatformApplication', // Specific to Blog-Platform-Backend
    'User', // Common entity classes to bootstrap
    'UserController',
    'UserService',
  ];

  console.log(`🔍 Trying class names:`, commonMainClassNames);

  for (const className of commonMainClassNames) {
    try {
      console.log(`   - Searching for class: ${className}`);
      const classResponse = await fetch(`${BACKEND_URL}/graph/classes/${encodeURIComponent(className)}`);
      if (classResponse.ok) {
        const classData = await classResponse.json();
        console.log(`✅ Found main class: ${classData.id}`);
        return classData.id; // Return the full class ID
      } else {
        console.log(`   ❌ Not found (${classResponse.status})`);
      }
    } catch (error) {
      // Continue trying other class names
      console.log(`   ❌ Error searching for ${className}:`, error);
      continue;
    }
  }

  console.warn('⚠️ No main class found in common patterns');
  return null;
}

// ---------------------------------------------------------------------------
// 4. Class & Method Lookups
// ---------------------------------------------------------------------------
export async function fetchClassByName(className: string): Promise<ClassResponse | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/graph/classes/${encodeURIComponent(className)}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchMethodsByName(methodName: string): Promise<MethodResponse[] | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/graph/methods/${encodeURIComponent(methodName)}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// 5. Class Deep Insights (Endpoints using class_id)
// ---------------------------------------------------------------------------
export async function fetchClassMethods(classId: string): Promise<MethodResponse[] | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/graph/classes/${encodeURIComponent(classId)}/methods`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchClassFields(classId: string): Promise<FieldResponse[] | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/graph/classes/${encodeURIComponent(classId)}/fields`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchClassHistory(classId: string): Promise<ClassHistoryResponse | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/graph/classes/${encodeURIComponent(classId)}/history`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchClassDependencies(classId: string): Promise<DependencyGroupResponse | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/graph/classes/${encodeURIComponent(classId)}/dependencies`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchChangeCoupling(): Promise<ChangeCouplingResponse | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/change-coupling/`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchClassDependents(classId: string): Promise<DependencyGroupResponse | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/graph/classes/${encodeURIComponent(classId)}/dependents`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchClassSubgraph(classId: string, repoName?: string) {
  try {
    const res = await fetch(`${BACKEND_URL}/graph/classes/${encodeURIComponent(classId)}/subgraph`);
    if (!res.ok) return null;
    const data = await res.json();
    return parseGraphDocument(data, repoName);
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Helper: Convert GraphDocument -> React Flow Nodes & Edges
// ---------------------------------------------------------------------------
function parseGraphDocument(data: any, repoName?: string) {
  const COLUMNS = 4;
  const X_SPACING = 280;
  const Y_SPACING = 160;

  const formattedNodes = data.nodes.map((node: any, index: number) => {
    const col = index % COLUMNS;
    const row = Math.floor(index / COLUMNS);
    const props = node.properties || {};
    const labelName = props.name || props.id || node.id;

    return {
      id: String(node.id),
      type: 'customNode',
      data: {
        label: labelName,
        category: String(node.label || props.type || 'class').toLowerCase(),
        subtext: props.package || node.label || 'Entity',
        modifiers: props.modifiers || [],
        annotations: props.annotations || [],
        rawProperties: props,
      },
      position: { x: 100 + col * X_SPACING, y: 100 + row * Y_SPACING },
    };
  });

  const formattedEdges = (data.relationships || []).map((rel: any, index: number) => ({
    id: `rel-${index}`,
    source: String(rel.source),
    target: String(rel.target),
    type: 'default',
    label: rel.type || 'CONTAINS',
    style: { stroke: '#243B6B', strokeWidth: 2 },
  }));

  return {
    nodes: formattedNodes,
    edges: formattedEdges,
    repoName: repoName || 'Connected Repo',
  };
}

export interface RAGResponse {
  answer: string;
  confidence: 'high' | 'medium' | 'low' | string;
  sources: string[];
}

export async function askRepoSense(
  question: string,
  topK: number = 3,
): Promise<RAGResponse> {
  const response = await fetch(`${BACKEND_URL}/rag/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      top_k: topK,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();

    throw new Error(
      `GraphRAG request failed: ${response.status} ${errorText}`,
    );
  }

  return await response.json();
}