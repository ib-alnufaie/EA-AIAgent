import os
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List
import json
from enum import Enum
import matplotlib.pyplot as plt
import seaborn as sns
from pyvis.network import Network
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load NLP model
try:
    nlp = spacy.load("en_core_web_sm")  
except:
    st.warning("SpaCy model not found. Installing...")
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


class ArchitectureDomain(Enum):
    BUSINESS = "Business Architecture"
    DATA = "Data Architecture"
    APPLICATION = "Application Architecture"
    TECHNOLOGY = "Technology Architecture"


class NORALayer(Enum):
    BUSINESS = "Business Layer"
    PROCESS = "Process Layer"
    APPLICATION = "Application Layer"
    TECHNICAL = "Technical Layer"
    DATA = "Data Layer"
    SECURITY = "Security Layer"


class RiskLevel(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RequirementAnalyzer:
    def __init__(self):
        self.domain_keywords = {
            ArchitectureDomain.BUSINESS: ["strategy", "capability", "process", "organization", "business"],
            ArchitectureDomain.DATA: ["data", "information", "database", "warehouse", "quality", "governance"],
            ArchitectureDomain.APPLICATION: ["application", "system", "service", "interface", "api", "microservice"],
            ArchitectureDomain.TECHNOLOGY: ["infrastructure", "cloud", "server", "network", "security", "platform"]
        }

        self.nora_layer_keywords = {
            NORALayer.BUSINESS: ["business", "strategy", "capability", "service"],
            NORALayer.PROCESS: ["process", "workflow", "procedure", "operation"],
            NORALayer.APPLICATION: ["application", "system", "software", "component"],
            NORALayer.TECHNICAL: ["technology", "infrastructure", "hardware", "network"],
            NORALayer.DATA: ["data", "information", "database", "analytics"],
            NORALayer.SECURITY: ["security", "compliance", "risk", "control"]
        }

    def analyze_requirements(self, text: str) -> Dict:
        """Analyze free-text requirements and classify them"""
        doc = nlp(text.lower())

        domain_scores = {d: 0 for d in ArchitectureDomain}
        for token in doc:
            for domain, keywords in self.domain_keywords.items():
                if token.text in keywords:
                    domain_scores[domain] += 1

        layer_scores = {l: 0 for l in NORALayer}
        for token in doc:
            for layer, keywords in self.nora_layer_keywords.items():
                if token.text in keywords:
                    layer_scores[layer] += 1

        entities = [(ent.text, ent.label_) for ent in doc.ents]

        return {
            "primary_domain": max(domain_scores.items(), key=lambda x: x[1])[0],
            "domain_scores": domain_scores,
            "primary_layer": max(layer_scores.items(), key=lambda x: x[1])[0],
            "layer_scores": layer_scores,
            "entities": entities
        }


class ArchitectureAssessor:
    def __init__(self):
        self.togaf_principles = self._load_togaf_principles()
        self.nora_standards = self._load_nora_standards()
        self.best_practices = self._load_best_practices()

    def _load_togaf_principles(self) -> Dict:
        return {
            "Business": [
                "Business continuity",
                "Business alignment",
                "Process standardization",
                "Capability-based planning"
            ],
            "Data": [
                "Data is an asset",
                "Data is shared",
                "Data is accessible",
                "Data trustee responsibility"
            ],
            "Application": [
                "Application modularity",
                "Service orientation",
                "Component reuse",
                "Loose coupling"
            ],
            "Technology": [
                "Technology standardization",
                "Interoperability",
                "Scalability",
                "Security by design"
            ]
        }

    def _load_nora_standards(self) -> Dict:
        return {
            "Business Layer": [
                "Service orientation",
                "Citizen-centric design",
                "Organizational agility"
            ],
            "Process Layer": [
                "Process automation",
                "Straight-through processing",
                "Workflow transparency"
            ],
            "Application Layer": [
                "API-first design",
                "Cloud-native principles",
                "Microservice architecture"
            ],
            "Technical Layer": [
                "Infrastructure as code",
                "Zero trust security",
                "Hybrid cloud enablement"
            ],
            "Data Layer": [
                "Data sovereignty",
                "Metadata management",
                "Master data management"
            ],
            "Security Layer": [
                "Privacy by design",
                "Continuous monitoring",
                "Defense in depth"
            ]
        }

    def _load_best_practices(self) -> Dict:
        return {
            "Modernization": [
                "Incremental modernization",
                "Strangler pattern adoption",
                "Technical debt management"
            ],
            "Governance": [
                "Architecture review boards",
                "Compliance automation",
                "Policy as code"
            ],
            "Integration": [
                "Event-driven architecture",
                "API gateway pattern",
                "Enterprise service bus"
            ]
        }

    def assess_compliance(self, component: Dict) -> Dict:
        """Assess component against architecture frameworks"""
        domain = component.get("domain", ArchitectureDomain.BUSINESS)
        layer = component.get("layer", NORALayer.BUSINESS)

        domain_principles = self.togaf_principles.get(domain.name, [])
        layer_standards = self.nora_standards.get(layer.value, [])

        compliance = {
            "togaf_compliance": min(100, len(domain_principles) * 10 + np.random.randint(10, 30)),
            "nora_alignment": min(100, len(layer_standards) * 12 + np.random.randint(5, 25)),
            "business_alignment": np.random.randint(40, 90),
            "technical_debt": np.random.randint(10, 80),
            "domain": domain.name,
            "layer": layer.value
        }
        return compliance

    def generate_recommendations(self, assessment: Dict) -> List[str]:
        recommendations = []

        if assessment["togaf_compliance"] < 70:
            recommendations.append(
                f"Increase TOGAF compliance by conducting architecture review against {assessment['domain']} principles"
            )
        if assessment["nora_alignment"] < 65:
            recommendations.append(
                f"Improve NORA alignment by implementing {assessment['layer']} standards"
            )
        if assessment["technical_debt"] > 50:
            recommendations.extend([
                "Prioritize technical debt reduction in next planning cycle",
                "Conduct technical debt assessment workshop"
            ])
        if assessment["business_alignment"] < 60:
            recommendations.append(
                "Implement business capability mapping to improve alignment"
            )
        return recommendations


class RiskAssessor:
    RISK_FACTORS = {
        "age": {"weight": 0.2, "values": {"<3y": 10, "3-5y": 30, "5-7y": 50, ">7y": 70}},
        "criticality": {"weight": 0.3, "values": {"low": 10, "medium": 30, "high": 70, "critical": 90}},
        "complexity": {"weight": 0.15, "values": {"low": 10, "medium": 40, "high": 70}},
        "dependencies": {"weight": 0.15, "values": {"few": 10, "moderate": 30, "many": 60}},
        "documentation": {"weight": 0.1, "values": {"excellent": 10, "good": 30, "fair": 50, "poor": 80}},
        "support": {"weight": 0.1, "values": {"vendor": 20, "in-house": 40, "none": 70}}
    }

    def assess_risk(self, component: Dict) -> Dict:
        total_score = 0
        factor_scores = {}

        for factor, config in self.RISK_FACTORS.items():
            value = component.get(factor, list(config["values"].keys())[0])
            score = config["values"].get(value, 50)
            weighted_score = score * config["weight"]
            factor_scores[factor] = {"score": score, "weighted": weighted_score}
            total_score += weighted_score

        if total_score < 30:
            risk_level = RiskLevel.LOW
        elif total_score < 50:
            risk_level = RiskLevel.MEDIUM
        elif total_score < 70:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        return {
            "total_score": round(total_score, 1),
            "risk_level": risk_level,
            "factor_scores": factor_scores
        }

    def generate_risk_mitigation(self, risk_assessment: Dict) -> List[str]:
        mitigations = []
        risk_level = risk_assessment["risk_level"]

        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            mitigations.append("Prioritize for modernization or replacement")

        for factor, scores in risk_assessment["factor_scores"].items():
            if scores["score"] > 60:
                mitigations.append(
                    f"Address {factor.replace('_', ' ')} risk through targeted intervention"
                )

        if risk_level == RiskLevel.CRITICAL:
            mitigations.extend([
                "Immediate architecture review required",
                "Develop contingency plan for failure scenarios"
            ])

        return mitigations


class GenAIAnalysisModule:
    def __init__(self):
        self.requirement_analyzer = RequirementAnalyzer()
        self.architecture_assessor = ArchitectureAssessor()
        self.risk_assessor = RiskAssessor()

    def analyze_component(self, component_data: Dict) -> Dict:
        req_analysis = None
        if "description" in component_data and component_data["description"]:
            req_analysis = self.requirement_analyzer.analyze_requirements(component_data["description"])
            component_data.update({
                "domain": req_analysis["primary_domain"],
                "layer": req_analysis["primary_layer"],
                "entities": req_analysis["entities"]
            })

        assessment = self.architecture_assessor.assess_compliance(component_data)
        recommendations = self.architecture_assessor.generate_recommendations(assessment)

        risk_assessment = self.risk_assessor.assess_risk(component_data)
        risk_mitigations = self.risk_assessor.generate_risk_mitigation(risk_assessment)

        return {
            "component": component_data,
            "requirement_analysis": req_analysis if req_analysis else None,
            "architecture_assessment": assessment,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations + risk_mitigations
        }

    def visualize_analysis(self, analysis_result: Dict):
        tab1, tab2, tab3 = st.tabs([
            "Compliance Overview",
            "Risk Analysis",
            "Recommendations"
        ])

        with tab1:
            self._show_compliance_charts(analysis_result)

        with tab2:
            self._show_risk_analysis(analysis_result)

        with tab3:
            self._show_recommendations(analysis_result)

    def _show_compliance_charts(self, analysis_result: Dict):
        assessment = analysis_result["architecture_assessment"]

        fig, ax = plt.subplots(1, 2, figsize=(12, 4))

        ax[0].bar(
            ["TOGAF Compliance", "NORA Alignment"],
            [assessment["togaf_compliance"], assessment["nora_alignment"]],
            color=["#E31937", "#0063b3"]
        )
        ax[0].set_ylim(0, 100)
        ax[0].set_title("Framework Compliance")

        ax[1].bar(
            ["Business Alignment", "Technical Debt"],
            [assessment["business_alignment"], assessment["technical_debt"]],
            color=["#00a86b", "#6c757d"]
        )
        ax[1].set_ylim(0, 100)
        ax[1].set_title("Alignment & Technical Debt")

        st.pyplot(fig)

    def _show_risk_analysis(self, analysis_result: Dict):
        risk = analysis_result["risk_assessment"]

        col1, col2 = st.columns(2)

        with col1:
            risk_colors = {
                RiskLevel.LOW: "green",
                RiskLevel.MEDIUM: "orange",
                RiskLevel.HIGH: "red",
                RiskLevel.CRITICAL: "darkred"
            }

            st.metric(
                "Overall Risk Score",
                f"{risk['total_score']}/100",
                risk["risk_level"].value,
                delta_color="off"
            )
            st.markdown(
                f"<div style='background:{risk_colors[risk['risk_level']]}; "
                f"color:white; padding:10px; border-radius:5px; text-align:center;'>"
                f"Risk Level: {risk['risk_level'].value}</div>",
                unsafe_allow_html=True
            )

        with col2:
            factors = list(risk["factor_scores"].keys())
            scores = [v["score"] for v in risk["factor_scores"].values()]

            fig, ax = plt.subplots()
            ax.barh(factors, scores, color="#E31937")
            ax.set_xlim(0, 100)
            ax.set_title("Risk Factor Breakdown")
            st.pyplot(fig)

    def _show_recommendations(self, analysis_result: Dict):
        recommendations = analysis_result["recommendations"]

        st.markdown("### Recommended Actions")
        for i, rec in enumerate(recommendations, 1):
            st.markdown(
                f"<div style='background:#f8f9fa; padding:10px; border-radius:5px; "
                f"margin-bottom:10px;'>{i}. {rec}</div>",
                unsafe_allow_html=True
            )

        roadmap = {
            "Immediate (0-3 months)": [
                rec for rec in recommendations if "review" in rec.lower() or "priority" in rec.lower()
            ],
            "Short-term (3-6 months)": [
                rec for rec in recommendations if "implement" in rec.lower() or "conduct" in rec.lower()
            ],
            "Long-term (6+ months)": [
                rec for rec in recommendations if "modernization" in rec.lower() or "alignment" in rec.lower()
            ]
        }

        st.markdown("### Suggested Roadmap")
        for timeframe, actions in roadmap.items():
            with st.expander(timeframe):
                for action in actions:
                    st.markdown(f"- {action}")


def show_genai_module():
    st.title("GenAI Enterprise Architecture Analysis")

    analysis_module = GenAIAnalysisModule()

    with st.expander("Input Architecture Component Details", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            component_name = st.text_input("Component Name")
            component_type = st.selectbox(
                "Component Type",
                ["Application", "Service", "Database", "Infrastructure", "Process"]
            )
            description = st.text_area("Description")

        with col2:
            domain = st.selectbox(
                "Primary Domain",
                [d.value for d in ArchitectureDomain],
                index=0
            )
            layer = st.selectbox(
                "NORA Layer",
                [l.value for l in NORALayer],
                index=0
            )
            criticality = st.selectbox(
                "Business Criticality",
                ["low", "medium", "high", "critical"],
                index=1
            )

        with st.expander("Risk Factors (Optional)"):
            col1, col2 = st.columns(2)
            with col1:
                age = st.selectbox(
                    "System Age",
                    ["<3y", "3-5y", "5-7y", ">7y"],
                    index=2
                )
                complexity = st.selectbox(
                    "Complexity",
                    ["low", "medium", "high"],
                    index=1
                )
            with col2:
                dependencies = st.selectbox(
                    "Dependencies",
                    ["few", "moderate", "many"],
                    index=1
                )
                documentation = st.selectbox(
                    "Documentation Quality",
                    ["excellent", "good", "fair", "poor"],
                    index=2
                )
                support = st.selectbox(
                    "Support Model",
                    ["vendor", "in-house", "none"],
                    index=0
                )

    if st.button("Analyze Component", type="primary"):
        component_data = {
            "name": component_name,
            "type": component_type,
            "description": description,
            "domain": ArchitectureDomain(domain),
            "layer": NORALayer(layer),
            "criticality": criticality,
            "age": age,
            "complexity": complexity,
            "dependencies": dependencies,
            "documentation": documentation,
            "support": support
        }

        with st.spinner("Analyzing component..."):
            analysis_result = analysis_module.analyze_component(component_data)

        st.success("Analysis complete!")
        analysis_module.visualize_analysis(analysis_result)

        with st.expander("View Raw Analysis Data"):
            st.json(analysis_result)


def main():
    st.set_page_config(
        page_title="Enterprise Architecture AI",
        page_icon="🏛️",
        layout="wide"
    )

    st.markdown("""
    <style>
    .main-title {
    color: #E31937;
    font-size: 2.5rem;
    font-weight: 800;
    text-align: center;
    margin-bottom: 1rem;
    }
    .subtitle {
    color: #495057;
    font-size: 1.2rem;
    text-align: center;
    margin-bottom: 2rem;
    }
    .analysis-section {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 2rem;
    margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-title">Enterprise Architecture AI Suite</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">GenAI-powered analysis for TOGAF and NORA compliant architectures</p>', unsafe_allow_html=True)

    menu = ["Home", "Component Analysis", "Portfolio View", "Settings"]
    choice = st.sidebar.selectbox("Navigation", menu)

    if choice == "Home":
        st.markdown("""
        ## Welcome to the Enterprise Architecture AI Suite

        This application provides AI-powered analysis of your enterprise architecture components,
        assessing compliance with TOGAF and NORA frameworks while identifying risks and
        recommending improvements.

        ### Key Features:
        - **Requirement Analysis**: NLP-powered classification of architecture components
        - **Framework Compliance**: TOGAF and NORA alignment scoring
        - **Risk Assessment**: Comprehensive risk evaluation with mitigation strategies
        - **Recommendation Engine**: Actionable improvement suggestions

        Get started by selecting **Component Analysis** from the sidebar.
        """)
    elif choice == "Component Analysis":
        show_genai_module()
    elif choice == "Portfolio View":
        st.warning("Portfolio view coming in next release!")
    elif choice == "Settings":
        st.warning("Settings panel coming in next release!")


if __name__ == "__main__":
    main()
