## **Problem Statement**

Large Language Models (LLMs) are increasingly being deployed in applications such as Retrieval-Augmented Generation (RAG), AI agents, and fine-tuned domain-specific systems. While traditional security tools remain effective for conventional software vulnerabilities, they are not designed to detect LLM-specific threats such as prompt injection, jailbreak attacks, indirect prompt injection, context manipulation, and sensitive information leakage.

Existing LLM security evaluation frameworks, including Garak, PyRIT, Promptfoo, and OpenAI Evals, have improved automated adversarial testing by identifying vulnerabilities and generating evaluation reports. However, developers still face challenges in consolidating findings from multiple tools, understanding how vulnerabilities relate to complex AI architectures, and selecting appropriate mitigation strategies for their specific deployment.

As AI systems become more complex and security-critical, there is a need for a unified security assessment platform that integrates results from multiple evaluation tools, maps vulnerabilities to standardized frameworks such as MITRE ATLAS, visualizes attack paths across AI components, and provides architecture-aware remediation recommendations. Such a platform would improve the efficiency, interpretability, and practical usability of AI security assessments before deployment.

### **Objectives**

The primary objective of **ATLAS-Scan** is to provide an automated, end-to-end security assessment platform that evaluates AI applications across diverse deployment configurations—including base LLMs, fine-tuned models, and RAG-enabled systems.  
Specifically, ATLAS-Scan aims to:

* **Automate Security Assessments** – Execute adversarial testing using Garak and PyRIT against deployed AI applications to identify prompt injection, jailbreak, context manipulation, and information leakage vulnerabilities.  
* **Compare AI Security Posture** – Evaluate and compare the security behavior of base models, fine-tuned models, and RAG-enabled systems using standardized security metrics.  
* **Contextualize Vulnerabilities** – Normalize scan results from multiple evaluation engines and map detected attacks to MITRE ATLAS tactics and techniques.  
* **Visualize Attack Relationships** – Generate interactive attack graphs illustrating the relationships between attacks, affected components, and mitigations.  
* **Provide Architecture-Aware Remediation** – Recommend mitigation strategies tailored to the detected vulnerabilities and the assessed AI deployment architecture.  
    
  


## **Feature List**

* **Automated Red Teaming Engine** – runs security tests using Garak (static/known vulnerability scans) and PyRIT (multi-turn conversational attacks)  
* **MITRE ATLAS Technique Mapping** – classifies each successful attack against the MITRE ATLAS taxonomy  
* **Attack Path Visualization** – a graph (via Neo4j) showing the sequence of steps from initial prompt to final exploit  
* **Remediation Roadmap** – links each mapped technique to fix-it guidance embedded in the visual map  
* **Scan history & comparison dashboard** – store past scan results per model/app so users can track whether a fix actually worked over time (regression tracking). This is a very natural add since you're already storing structured results.  
* **Exportable reports (PDF/CSV)** – let users download a scan summary for compliance or handoff to a security team. Low effort, high perceived value in a security tool.  
* **Custom attack/prompt upload** – allow users to supply their own test prompts alongside Garak/PyRIT's built-in probes, for org-specific threat scenarios.  
* **Comparison view** – side-by-side vulnerability comparison across two or more models/configs   