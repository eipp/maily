# Architecture Diagram

## High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend"
        Web["Web Frontend\n(Next.js)"]
        subgraph "Canvas Enhancement"
            CC["Cognitive Canvas"]
            VL["Visualization Layers"]
            RT["Real-time Collaboration"]
        end
    end

    subgraph "Backend Services"
        API["API Service\n(FastAPI)"]
        AI["AI Service\n(FastAPI)"]
        Email["Email Service\n(Node.js)"]
        Campaign["Campaign Service\n(Node.js)"]
        Analytics["Analytics Service\n(Node.js)"]
        
        subgraph "AI Mesh Network"
            AC["Agent Coordinator"]
            CA["Content Agent"]
            DA["Design Agent"]
            AA["Analytics Agent"]
            PA["Personalization Agent"]
            SM["Shared Memory"]
        end
        
        subgraph "Trust Verification"
            BS["Blockchain Service"]
            CS["Certificate Service"]
            TS["Token Service"]
            QR["QR Code Service"]
        end
        
        subgraph "Predictive Analytics"
            DAS["Data Aggregation Service"]
            PS["Prediction Service"]
            RS["Recommendation Service"]
            CFS["Confidence Service"]
        end
    end
    
    subgraph "Infrastructure"
        Redis["Redis v7.0.5"]
        RabbitMQ["RabbitMQ v3.12.0"]
        K8s["Kubernetes"]
        Prometheus["Prometheus"]
        Blockchain["Polygon Blockchain"]
    end
    
    %% Frontend connections
    Web --> API
    CC --> API
    VL --> API
    RT --> API
    
    %% Service connections
    API --> AI
    API --> Email
    API --> Campaign
    API --> Analytics
    
    %% AI Mesh Network connections
    AI --> AC
    AC --> CA
    AC --> DA
    AC --> AA
    AC --> PA
    CA --> SM
    DA --> SM
    AA --> SM
    PA --> SM
    
    %% Trust Verification connections
    Email --> BS
    Email --> CS
    Campaign --> BS
    Campaign --> CS
    BS --> Blockchain
    CS --> QR
    CS --> TS
    
    %% Predictive Analytics connections
    Analytics --> DAS
    Analytics --> PS
    Analytics --> RS
    Analytics --> CFS
    
    %% Infrastructure connections
    SM --> Redis
    AC --> RabbitMQ
    DAS --> RabbitMQ
    K8s --> API
    K8s --> AI
    K8s --> Email
    K8s --> Campaign
    K8s --> Analytics
    Prometheus --> API
    Prometheus --> AI
    Prometheus --> Email
    Prometheus --> Campaign
    Prometheus --> Analytics
```

## Cognitive Canvas Architecture

```mermaid
graph TB
    subgraph "Frontend"
        CC["Cognitive Canvas Component"]
        DnD["React DnD"]
        Yjs["Yjs Collaboration"]
        
        subgraph "Visualization Layers"
            AIL["AI Reasoning Layer"]
            PIL["Performance Insights Layer"]
            TVL["Trust Verification Layer"]
        end
        
        subgraph "Controls"
            LC["Layer Controls"]
            TC["Tool Controls"]
            SC["Sharing Controls"]
        end
    end
    
    subgraph "Backend"
        CR["Canvas Router"]
        VS["Visualization Service"]
        PIS["Performance Insights Service"]
        TVS["Trust Verification Service"]
        WS["WebSocket Service"]
    end
    
    subgraph "Integration"
        AIS["AI Service"]
        AS["Analytics Service"]
        BS["Blockchain Service"]
    end
    
    %% Frontend connections
    CC --> DnD
    CC --> Yjs
    CC --> AIL
    CC --> PIL
    CC --> TVL
    CC --> LC
    CC --> TC
    CC --> SC
    
    %% Backend connections
    CR --> VS
    CR --> PIS
    CR --> TVS
    CR --> WS
    
    %% Integration connections
    VS --> AIS
    PIS --> AS
    TVS --> BS
    
    %% Frontend-Backend connections
    CC --> CR
    AIL --> VS
    PIL --> PIS
    TVL --> TVS
    Yjs --> WS
```

## AI Mesh Network Architecture

```mermaid
graph TB
    subgraph "AI Service"
        AC["Agent Coordinator"]
        
        subgraph "Specialized Agents"
            CA["Content Agent"]
            DA["Design Agent"]
            AA["Analytics Agent"]
            PA["Personalization Agent"]
        end
        
        subgraph "Core Components"
            SM["Shared Memory"]
            MFC["Model Fallback Chain"]
            CSF["Content Safety Filter"]
            CS["Confidence Scoring"]
        end
    end
    
    subgraph "Models"
        Claude["Claude 3.7 Sonnet"]
        GPT["GPT-4o"]
        Gemini["Gemini 2.0"]
    end
    
    subgraph "Infrastructure"
        Redis["Redis"]
        MQ["Message Queue"]
    end
    
    subgraph "Integration"
        API["API Service"]
        Email["Email Service"]
        Campaign["Campaign Service"]
        Analytics["Analytics Service"]
    end
    
    %% Agent connections
    AC --> CA
    AC --> DA
    AC --> AA
    AC --> PA
    
    %% Core component connections
    CA --> SM
    DA --> SM
    AA --> SM
    PA --> SM
    CA --> MFC
    DA --> MFC
    AA --> MFC
    PA --> MFC
    CA --> CSF
    DA --> CSF
    AA --> CSF
    PA --> CSF
    CA --> CS
    DA --> CS
    AA --> CS
    PA --> CS
    
    %% Model connections
    MFC --> Claude
    MFC --> GPT
    MFC --> Gemini
    
    %% Infrastructure connections
    SM --> Redis
    AC --> MQ
    
    %% Integration connections
    API --> AC
    Email --> AC
    Campaign --> AC
    Analytics --> AC
```

## Interactive Trust Verification Architecture

```mermaid
graph TB
    subgraph "Trust Verification"
        BS["Blockchain Service"]
        CS["Certificate Service"]
        TS["Token Service"]
        QRS["QR Code Service"]
    end
    
    subgraph "Blockchain"
        SC["Smart Contracts"]
        MS["Multi-Signature"]
        OR["Oracles"]
        FV["Formal Verification"]
    end
    
    subgraph "Frontend"
        CD["Certificate Display"]
        QRD["QR Code Display"]
        WI["Wallet Integration"]
        VI["Verification Indicators"]
    end
    
    subgraph "Integration"
        Email["Email Service"]
        Campaign["Campaign Service"]
        Analytics["Analytics Service"]
    end
    
    %% Trust Verification connections
    BS --> SC
    BS --> MS
    BS --> OR
    BS --> FV
    CS --> BS
    TS --> BS
    QRS --> CS
    
    %% Frontend connections
    CD --> CS
    QRD --> QRS
    WI --> BS
    WI --> TS
    VI --> BS
    
    %% Integration connections
    Email --> BS
    Email --> CS
    Email --> QRS
    Campaign --> BS
    Campaign --> CS
    Campaign --> TS
    Analytics --> BS
    Analytics --> TS
```

## Predictive Analytics Fusion Architecture

```mermaid
graph TB
    subgraph "Predictive Analytics"
        DAS["Data Aggregation Service"]
        PS["Prediction Service"]
        RS["Recommendation Service"]
        CFS["Confidence Service"]
    end
    
    subgraph "Data Sources"
        ES["Email Service"]
        CS["Campaign Service"]
        WS["Web Service"]
        EXS["External Sources"]
    end
    
    subgraph "Models"
        EPM["Email Performance Model"]
        AEM["Audience Engagement Model"]
        CEM["Content Effectiveness Model"]
    end
    
    subgraph "Frontend"
        AD["Analytics Dashboard"]
        RD["Recommendation Display"]
        CI["Confidence Indicators"]
        MDS["Multi-platform Data Selector"]
    end
    
    subgraph "Infrastructure"
        TSDB["Time Series Database"]
        Cache["Redis Cache"]
        K8s["Kubernetes"]
    end
    
    %% Predictive Analytics connections
    DAS --> PS
    DAS --> RS
    PS --> CFS
    RS --> CFS
    
    %% Data Source connections
    DAS --> ES
    DAS --> CS
    DAS --> WS
    DAS --> EXS
    
    %% Model connections
    PS --> EPM
    PS --> AEM
    PS --> CEM
    
    %% Frontend connections
    AD --> PS
    AD --> RS
    AD --> CFS
    RD --> RS
    CI --> CFS
    MDS --> DAS
    
    %% Infrastructure connections
    DAS --> TSDB
    PS --> Cache
    RS --> Cache
    K8s --> DAS
    K8s --> PS
    K8s --> RS
    K8s --> CFS
```
