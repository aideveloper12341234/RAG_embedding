flowchart TB
    STARTDOC["START HERE · Document ingestion"]
    STARTRET["START HERE · Retrieval"]

    subgraph CORP["1 · Corporate / ViewPoint Environment"]
        direction LR
        VP["Dispatcher · ViewPoint"]
        DB[("ViewPoint DB<br/>Read-only context")]
        RESULT["Cited recommendations<br/>or manual escalation"]
    end

    subgraph HOST["2 · Azure Hosting Environment"]
        direction TB

        subgraph INGEST["PIPELINE A · Daily document ingestion"]
            DAILY["Container Apps Job<br/>Daily scheduled run"]
            PREP["Extract + chunk documents<br/>Preserve source, version + permissions"]
            STORE["Store chunks + vectors + metadata<br/>Update / delete stale index entries"]
            DAILY ==> PREP
        end

        subgraph RUNTIME["PIPELINE B · Live retrieval and response"]
            APP["MAIN FASTAPI APPLICATION<br/>Azure Container App<br/>Authenticate + enrich alarm context<br/>Warm replicas · Autoscaling · Timeouts"]
            QUERY["Build retrieval query<br/>Alarm mapping + permission filters"]
            VALIDATE["Validate grounding + citations<br/>Insufficient evidence → escalate"]
            FALLBACK["Failure / timeout<br/>Continue existing ViewPoint workflow"]
            APP ==> QUERY
        end
    end

    subgraph AI["3 · Azure AI & Knowledge Retrieval"]
        direction TB
        EMBED["Azure OpenAI<br/>Document embeddings"]
        QEMBED["Azure OpenAI<br/>Query embedding"]
        SEARCH[("Azure AI Search<br/>Stored chunks + vectors + metadata<br/>Hybrid search + access filters")]
        LLM["Azure OpenAI<br/>Generate from retrieved evidence"]
    end

    subgraph EDP["4 · EDP / Databricks"]
        direction LR
        DOCS["New / updated approved documents<br/>EDP knowledge interface"]
        MAP["Alarm-to-document mappings"]
        DATA["Governed alarm history<br/>Unity Catalog → Databricks → Power BI"]
    end

    subgraph SEC["5 · Identity, Security & Data Governance"]
        SECURITY["Entra ID · Managed identities · Key Vault<br/>Least privilege · Private connectivity<br/>Document permissions · Audit · Retention"]
    end

    subgraph OPS["6 · Monitoring, Operations & DevOps"]
        MON["Azure Monitor · App Insights<br/>Latency · Cost · Index freshness · AI quality<br/>Daily job status + alerts"]
        DEPLOY["CI/CD · Infrastructure as code<br/>Rollback · Recovery targets + tests"]
    end

    DOCS ==>|"Daily ingestion"| DAILY
    PREP ==> EMBED
    EMBED ==> STORE
    STORE ==>|"Write index"| SEARCH

    VP -->|"Alarm + attributes"| APP
    APP <-->|"Context · Bounded timeout"| DB
    MAP --> QUERY
    QUERY ==> QEMBED
    QEMBED ==>|"Vector + text query + filters"| SEARCH
    SEARCH ==>|"Relevant chunks + citations"| LLM
    LLM ==> VALIDATE
    VALIDATE ==>|"Validated recommendations"| RESULT
    APP --> FALLBACK
    VALIDATE -->|"Unsupported answer"| FALLBACK
    FALLBACK --> RESULT

    SECURITY -.-> APP
    SECURITY -.-> DAILY
    SECURITY -.-> SEARCH
    APP -.-> MON
    DAILY -.-> MON
    DEPLOY -.-> APP
    DEPLOY -.-> DAILY

    STARTDOC --> DOCS
    STARTRET --> VP

    classDef existing fill:#F1F5F9,stroke:#64748B,color:#172033;
    classDef changed fill:#FFF0D9,stroke:#E58200,stroke-width:2px,color:#332000;
    classDef main fill:#FFE0A6,stroke:#D56500,stroke-width:5px,color:#201000,font-size:18px,font-weight:bold;
    classDef docStart fill:#FFEDD5,stroke:#E58200,stroke-width:3px,color:#9A3412,font-weight:bold;
    classDef retrievalStart fill:#DCFCE7,stroke:#16A34A,stroke-width:3px,color:#166534,font-weight:bold;

    class VP,DB,RESULT,MAP,DATA existing;
    class DOCS,DAILY,PREP,EMBED,STORE,QUERY,QEMBED,SEARCH,LLM,VALIDATE,FALLBACK,SECURITY,MON,DEPLOY changed;
    class APP main;
    class STARTDOC docStart;
    class STARTRET retrievalStart;

    style CORP fill:#F8FAFC,stroke:#475569,stroke-width:2px
    style HOST fill:#EFF6FF,stroke:#2563EB,stroke-width:3px
    style AI fill:#FAF5FF,stroke:#9333EA,stroke-width:2px
    style EDP fill:#F0FDF4,stroke:#16A34A,stroke-width:2px
    style SEC fill:#FFFBEB,stroke:#A16207,stroke-width:2px
    style OPS fill:#ECFEFF,stroke:#0891B2,stroke-width:2px
    style INGEST fill:#FFF7ED,stroke:#E58200,stroke-width:3px
    style RUNTIME fill:#FFF7ED,stroke:#E58200,stroke-width:3px

    linkStyle 0,2,3,4,5,24 stroke:#E58200,stroke-width:3px
    linkStyle 1,6,7,8,9,10,11,12,13,14,15,16,25 stroke:#16A34A,stroke-width:3px