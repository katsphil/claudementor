#!/usr/bin/env python3
"""
Section prompt templates for mentoring report generation.
Each function returns a detailed prompt for generating that section via Task agent.
"""

def get_section_prompt(section_num, company_info, relevant_files):
    """
    Get the appropriate prompt for a given section number.

    Args:
        section_num: Section number (1-11)
        company_info: Dict with company_name, company_afm, company_kad
        relevant_files: List of file paths relevant to this section

    Returns:
        Detailed prompt string for Task agent
    """

    prompts = {
        1: get_section_1_prompt,
        2: get_section_2_prompt,
        3: get_section_3_prompt,
        4: get_section_4_prompt,
        5: get_section_5_prompt,
        6: get_section_6_prompt,
        7: get_section_7_prompt,
        8: get_section_8_prompt,
        9: get_section_9_prompt,
        10: get_section_10_prompt,
        11: get_section_11_prompt
    }

    return prompts[section_num](section_num, company_info, relevant_files)

def get_section_1_prompt(section_num, company_info, relevant_files):
    return f"""Generate **Section 1: Business Profile & Strategic Positioning** for a Greek SME mentoring report.

**CRITICAL**: Save your response as section_{section_num}_generated.json in the current working directory.

**Relevant Files**: {', '.join([f.name for f in relevant_files]) if relevant_files else 'General business context'}

**Your Task**: Generate a comprehensive 800-1200 word section with:

**IMPORTANT - Language**: Think and analyze in English for clarity, but write ALL final output content in Greek. Technical terms may remain in English where appropriate (e.g., "SEO", "CRM", "ROI").

**IMPORTANT - Metadata Extraction**: Extract the following from business documents (E1, E3, business plans, extra-info files, etc.):
   - **company_name**: Full legal business name
   - **afm**: Greek tax identification number (9 digits)
   - **kad**: Greek business activity code (ΚΑΔ format: XX.XX.XX.XX)
   - **website**: Company website URL (check extra-info file if not found elsewhere, leave empty string if not found)

1. **Content (HTML formatted)** covering:
   - Detailed business model analysis
   - Market positioning suggestions
   - Regulatory compliance guidance (Greek regulations, professional associations)
   - Ownership structure analysis
   - Brand development recommendations
   - Competitive differentiation strategies
   - Strategic partnerships and assets

2. **KPIs** (3-6 items): Business structure metrics, industry positioning

3. **Tables** (if relevant): SWOT analysis, business model canvas

4. **Action Items** (3-6 items): Specific, actionable steps with timelines, owners, and costs

**Style**: Act as a senior business mentor providing extensive, personalized guidance. Be verbose, detailed, and actionable.

**Output Format**: Return ONLY valid JSON:
```json
{{
  "number": 1,
  "title": "Business Profile & Strategic Positioning",
  "metadata": {{
    "company_name": "Extracted company name",
    "afm": "123456789",
    "kad": "XX.XX.XX.XX",
    "website": "https://example.com"
  }},
  "content": "HTML formatted content...",
  "kpis": [{{"label": "...", "value": "..."}}],
  "tables": [{{"title": "...", "headers": [...], "rows": [[...]]}}],
  "action_items": [{{"action": "...", "timeline": "...", "owner": "...", "cost": "..."}}]
}}
```

Read any available documents and generate comprehensive analysis now."""

def get_section_2_prompt(section_num, company_info, relevant_files):
    return f"""Generate **Section 2: Financial Health & Performance Optimization** for Greek SME mentoring report.

**CRITICAL**: Save your response as section_{section_num}_generated.json in the current working directory.

**Company**: {company_info.get('company_name', 'Greek SME')} (AFM: {company_info.get('afm', 'N/A')})

**Relevant Files**: {', '.join([f.name for f in relevant_files]) if relevant_files else 'Financial data to be analyzed'}

**Your Task**: Generate comprehensive 800-1200 word financial analysis with:

**IMPORTANT - Language**: Think and analyze in English for clarity, but write ALL final output content in Greek. Technical terms may remain in English where appropriate (e.g., "SEO", "CRM", "ROI").

1. **Content (HTML formatted)**:
   - Revenue analysis and cash flow assessment
   - **Teiresias Credit Score**: Search Excel files (especially "sorefsis") for credit scores in tables with headers like "Βαθμολογία", "Score", "Rating". Common formats: "450/600", "Grade A-E". Explain in Greek SME context (e.g., "450/600 = top 25% of Greek SMEs"). Provide improvement strategies.
   - Financial ratios analysis (profit margin, liquidity, working capital, debt service coverage)
   - Cost structure analysis with recommendations
   - Tax compliance status (from E1, E3 declarations if available)

2. **KPIs** (5-7 items): Revenue, profit margins, Teiresias credit score (if found), liquidity ratios

3. **Tables** (2-3):
   - Financial ratios vs. industry benchmarks
   - Monthly cash flow projections
   - Cost breakdown analysis

4. **Action Items** (4-6 items): Credit score improvement, financial management, accounting software, credit line

**CRITICAL - Output Format**: Return ONLY valid JSON with this EXACT structure:
```json
{{
  "number": 2,
  "title": "Financial Health & Performance Optimization",
  "content": "<div>HTML formatted content in Greek...</div>",
  "kpis": [
    {{"label": "KPI label in Greek", "value": "value with units", "target": "optional target", "status": "optional status"}}
  ],
  "tables": [
    {{"title": "Table title in Greek", "headers": ["Column 1", "Column 2", "..."], "rows": [["Cell 1,1", "Cell 1,2", "..."], ["Cell 2,1", "Cell 2,2", "..."]]}}
  ],
  "action_items": [
    {{"title": "Action title in Greek", "priority": "Υψηλή|Μέτρια|Χαμηλή", "timeline": "X μήνες", "description": "Detailed description in Greek", "expected_impact": "Expected results in Greek", "resources_needed": "Required resources in Greek"}}
  ]
}}
```

**MANDATORY**: Use "number": 2 (not "section"), use "label" for KPIs, use "title" for action_items."""

def get_section_3_prompt(section_num, company_info, relevant_files):
    return f"""Generate **Section 3: Market Analysis & Competitive Strategy** for Greek SME.

**CRITICAL**: Save your response as section_{section_num}_generated.json in the current working directory.

**Company**: {company_info.get('company_name', 'Greek SME')} (AFM: {company_info.get('afm', 'N/A')})

**Your Task**: Generate 800-1200 word market analysis with:

**IMPORTANT - Language**: Think and analyze in English for clarity, but write ALL final output content in Greek. Technical terms may remain in English where appropriate (e.g., "SEO", "CRM", "ROI").

1. **Content (HTML)**:
   - Greek market size and trends for this industry (KAD: {company_info.get('kad', 'N/A')})
   - Competitive landscape assessment (5 competitor types)
   - Target market segmentation (4-5 distinct segments)
   - Differentiation strategies
   - Pricing strategy recommendations
   - Market positioning tactics
   - Insurance/partnership opportunities
   - Local vs regional expansion analysis

2. **KPIs** (5-6): Market size (TAM), competitive density, market share targets, LTV

3. **Tables** (2):
   - Competitive analysis matrix (5 rows)
   - Target segments with demographics and strategy

4. **Action Items** (5-6): Competitive intelligence, pricing analysis, partnership development

**CRITICAL - Output Format**: Return ONLY valid JSON with this EXACT structure:
```json
{{
  "number": 3,
  "title": "Market Analysis & Competitive Strategy",
  "content": "<div>HTML formatted content in Greek...</div>",
  "kpis": [
    {{"label": "KPI label in Greek", "value": "value with units"}}
  ],
  "tables": [
    {{"title": "Table title in Greek", "headers": ["Column 1", "Column 2", "..."], "rows": [["Cell 1,1", "Cell 1,2", "..."], ["Cell 2,1", "Cell 2,2", "..."]]}}
  ],
  "action_items": [
    {{"title": "Action title in Greek", "priority": "Υψηλή|Μέτρια|Χαμηλή", "timeline": "X μήνες", "description": "Detailed description in Greek", "expected_impact": "Expected results in Greek", "resources_needed": "Required resources in Greek"}}
  ]
}}
```

**MANDATORY**: Use "number": 3 (not "section"), use "label" for KPIs, use "title" for action_items."""

def get_section_4_prompt(section_num, company_info, relevant_files):
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')

    return f"""Generate **Section 4: Funding Strategy & Investment Planning** for Greek SME.

**CRITICAL**: Save your response as section_{section_num}_generated.json in the current working directory.

**Company**: {company_info.get('company_name', 'Greek SME')}
**Relevant Files**: {', '.join([f.name for f in relevant_files]) if relevant_files else 'Funding proposals if available'}
**Today's Date**: {current_date}

**Your Task**: Generate 800-1200 words on:

**IMPORTANT - Language**: Think and analyze in English for clarity, but write ALL final output content in Greek. Technical terms may remain in English where appropriate (e.g., "ΕΣΠΑ", "ROI", "crowdfunding").

1. **Content (HTML)**:
   - ΕΣΠΑ 2021-2027 program analysis (5+ relevant programs)
     Use WebSearch to verify current program availability on espa.gr
     Only include programs with open calls or upcoming deadlines after {current_date}
     Include verified submission deadlines from live sources
   - Traditional bank financing options
   - Alternative financing (crowdfunding, angel investors, leasing)
   - ROI calculations for proposed investments
   - Step-by-step loan application guidance
   - Risk mitigation strategies
   - Investment prioritization framework

2. **KPIs** (4-5): Available ΕΣΠΑ programs, loan capacity, ROI projections

3. **Tables** (2):
   - ΕΣΠΑ programs comparison (eligibility, amounts, verified timelines)
   - Investment options with ROI analysis

4. **Action Items** (4-5): ΕΣΠΑ application, bank negotiations, investment plan

**CRITICAL - Output Format**: Return ONLY valid JSON with this EXACT structure:
```json
{{
  "number": 4,
  "title": "Funding Strategy & Investment Planning",
  "content": "<div>HTML formatted content in Greek...</div>",
  "kpis": [
    {{"label": "KPI label in Greek", "value": "value with units"}}
  ],
  "tables": [
    {{"title": "Table title in Greek", "headers": ["Column 1", "Column 2", "..."], "rows": [["Cell 1,1", "Cell 1,2", "..."], ["Cell 2,1", "Cell 2,2", "..."]]}}
  ],
  "action_items": [
    {{"title": "Action title in Greek", "priority": "Υψηλή|Μέτρια|Χαμηλή", "timeline": "X μήνες", "description": "Detailed description in Greek", "expected_impact": "Expected results in Greek", "resources_needed": "Required resources in Greek"}}
  ]
}}
```

**MANDATORY**: Use "number": 4 (not "section"), use "label" for KPIs, use "title" for action_items."""

def get_section_5_prompt(section_num, company_info, relevant_files):
    return f"""Generate **Section 5: Digital Transformation Roadmap** for Greek SME.

**CRITICAL**: Save your response as section_{section_num}_generated.json in the current working directory.

**Company**: {company_info.get('company_name', 'Greek SME')}

**Your Task**: Generate 800-1200 words on digital transformation:

**IMPORTANT - Language**: Think and analyze in English for clarity, but write ALL final output content in Greek. Technical terms may remain in English where appropriate (e.g., "SEO", "CRM", "UX", "WordPress").

1. **Content (HTML)**:
   - **Website Discovery**: Systematically search business plan, proposals, and contact documents for website URLs. Check: company info sections, contact details, marketing sections, headers/footers, email signatures. Look for patterns: www., http://, .gr, .com domains.
   - IF website found: Use WebSearch tool to analyze site (performance, SEO, mobile, UX) and provide specific improvement recommendations with costs.
   - IF no website: Provide greenfield implementation plan with platform recommendations, timeline, and budget.
   - Digital maturity assessment based on findings
   - Online booking/CRM systems recommendations
   - Social media strategy
   - Email marketing automation
   - Digital payment systems
   - SEO and online visibility plan

2. **KPIs** (4-5): Digital maturity score, online visibility, website metrics

3. **Tables** (1-2):
   - Digital transformation roadmap (phases, timeline, costs)
   - Tool recommendations comparison

4. **Action Items** (5-6): Website development/improvement, social media, CRM, SEO

**CRITICAL - Output Format**: Return ONLY valid JSON with this EXACT structure:
```json
{{
  "number": 5,
  "title": "Digital Transformation Roadmap",
  "content": "<div>HTML formatted content in Greek...</div>",
  "kpis": [
    {{"label": "KPI label in Greek", "value": "value with units"}}
  ],
  "tables": [
    {{"title": "Table title in Greek", "headers": ["Column 1", "Column 2", "..."], "rows": [["Cell 1,1", "Cell 1,2", "..."], ["Cell 2,1", "Cell 2,2", "..."]]}}
  ],
  "action_items": [
    {{"title": "Action title in Greek", "priority": "Υψηλή|Μέτρια|Χαμηλή", "timeline": "X μήνες", "description": "Detailed description in Greek", "expected_impact": "Expected results in Greek", "resources_needed": "Required resources in Greek"}}
  ]
}}
```

**MANDATORY**: Use "number": 5 (not "section"), use "label" for KPIs, use "title" for action_items."""

def get_section_6_prompt(section_num, company_info, relevant_files):
    return f"""Generate **Section 6: Financial Management Systems** for Greek SME.

**CRITICAL**: Save your response as section_{section_num}_generated.json in the current working directory.

**Company**: {company_info.get('company_name', 'Greek SME')}
**Relevant Files**: {', '.join([f.name for f in relevant_files]) if relevant_files else 'Financial system data'}

**Your Task**: Generate 800-1200 words on financial systems:

**IMPORTANT - Language**: Think and analyze in English for clarity, but write ALL final output content in Greek. Technical terms may remain in English where appropriate (e.g., "ERP", "myDATA", "dashboard").

1. **Content (HTML)**:
   - Current systems assessment
   - Greek accounting software comparison (SingularLogic, SoftOne, Epsilon Net)
   - ERP system recommendations
   - myDATA integration requirements
   - Digital invoicing compliance
   - Financial dashboard design
   - Process automation opportunities
   - Training curriculum for staff

2. **KPIs** (3-5): Automation level, compliance status, processing time

3. **Tables** (2):
   - Software comparison matrix (features, costs, pros/cons)
   - Implementation timeline with milestones

4. **Action Items** (4-5): Software selection, implementation, training

**CRITICAL - Output Format**: Return ONLY valid JSON with this EXACT structure:
```json
{{
  "number": 6,
  "title": "Financial Management Systems",
  "content": "<div>HTML formatted content in Greek...</div>",
  "kpis": [
    {{"label": "KPI label in Greek", "value": "value with units"}}
  ],
  "tables": [
    {{"title": "Table title in Greek", "headers": ["Column 1", "Column 2", "..."], "rows": [["Cell 1,1", "Cell 1,2", "..."], ["Cell 2,1", "Cell 2,2", "..."]]}}
  ],
  "action_items": [
    {{"title": "Action title in Greek", "priority": "Υψηλή|Μέτρια|Χαμηλή", "timeline": "X μήνες", "description": "Detailed description in Greek", "expected_impact": "Expected results in Greek", "resources_needed": "Required resources in Greek"}}
  ]
}}
```

**MANDATORY**: Use "number": 6 (not "section"), use "label" for KPIs, use "title" for action_items."""

def get_section_7_prompt(section_num, company_info, relevant_files):
    return f"""Generate **Section 7: ESG Implementation Framework** for Greek SME.

**CRITICAL**: Save your response as section_{section_num}_generated.json in the current working directory.

**Company**: {company_info.get('company_name', 'Greek SME')}

**Your Task**: Generate 800-1200 words on ESG:

**IMPORTANT - Language**: Think and analyze in English for clarity, but write ALL final output content in Greek. Technical terms may remain in English where appropriate (e.g., "ESG", "ISO", "B-Corp", "ROI").

1. **Content (HTML)**:
   - ESG scorecard (Environmental, Social, Governance - base 100)
   - Specific deficiencies and improvement opportunities
   - Energy efficiency initiatives with ROI
   - Waste reduction programs
   - Social responsibility initiatives
   - Governance improvements
   - Connection to Greek funding opportunities
   - Implementation timeline with costs
   - Certification pathways (ISO, B-Corp, etc.)

2. **KPIs** (4-6): ESG scores (E/S/G), energy savings targets, carbon footprint

3. **Tables** (2):
   - ESG assessment scorecard
   - Initiative ROI analysis

4. **Action Items** (5-6): Energy audit, waste management, governance policies

**CRITICAL - Output Format**: Return ONLY valid JSON with this EXACT structure:
```json
{{
  "number": 7,
  "title": "ESG Implementation Framework",
  "content": "<div>HTML formatted content in Greek...</div>",
  "kpis": [
    {{"label": "KPI label in Greek", "value": "value with units"}}
  ],
  "tables": [
    {{"title": "Table title in Greek", "headers": ["Column 1", "Column 2", "..."], "rows": [["Cell 1,1", "Cell 1,2", "..."], ["Cell 2,1", "Cell 2,2", "..."]]}}
  ],
  "action_items": [
    {{"title": "Action title in Greek", "priority": "Υψηλή|Μέτρια|Χαμηλή", "timeline": "X μήνες", "description": "Detailed description in Greek", "expected_impact": "Expected results in Greek", "resources_needed": "Required resources in Greek"}}
  ]
}}
```

**MANDATORY**: Use "number": 7 (not "section"), use "label" for KPIs, use "title" for action_items."""

def get_section_8_prompt(section_num, company_info, relevant_files):
    return f"""Generate **Section 8: AI & Innovation Strategy** for Greek SME.

**CRITICAL**: Save your response as section_{section_num}_generated.json in the current working directory.

**Company**: {company_info.get('company_name', 'Greek SME')} (Industry: {company_info.get('kad', 'N/A')})

**Your Task**: Generate 800-1200 words on AI/innovation:

**IMPORTANT - Language**: Think and analyze in English for clarity, but write ALL final output content in Greek. Technical terms may remain in English where appropriate (e.g., "AI", "machine learning", "automation", "ChatGPT").

1. **Content (HTML)**:
   - AI readiness assessment (detailed, current state)
   - Industry-specific AI tool recommendations
   - Implementation strategy with phases
   - Change management guidance
   - Training and upskilling programs
   - Innovation culture development
   - Cost-benefit analysis for AI adoption
   - Risk assessment and mitigation

2. **KPIs** (4-5): AI readiness score, automation potential, efficiency gains

3. **Tables** (1): AI tools comparison for this industry

4. **Action Items** (4-5): AI pilot project, training, tool implementation

5. **VIDEO RECOMMENDATIONS** (EXACTLY 5):
   - MANDATORY: Use the WebSearch tool to search YouTube for real, existing videos
   - Search queries should be specific to AI/business applications for SMEs
   - Verify each video exists before including it in your response
   - Include 5 YouTube videos with: title, channel, url, duration, topic, relevance to this specific business
   - Focus on practical AI/business applications for Greek SMEs
   - Only include videos you have confirmed exist through WebSearch

**CRITICAL - Output Format**: Return ONLY valid JSON with this EXACT structure:
```json
{{
  "number": 8,
  "title": "AI & Innovation Strategy",
  "content": "<div>HTML formatted content in Greek...</div>",
  "kpis": [
    {{"label": "KPI label in Greek", "value": "value with units"}}
  ],
  "tables": [
    {{"title": "Table title in Greek", "headers": ["Column 1", "Column 2", "..."], "rows": [["Cell 1,1", "Cell 1,2", "..."], ["Cell 2,1", "Cell 2,2", "..."]]}}
  ],
  "action_items": [
    {{"title": "Action title in Greek", "priority": "Υψηλή|Μέτρια|Χαμηλή", "timeline": "X μήνες", "description": "Detailed description in Greek", "expected_impact": "Expected results in Greek", "resources_needed": "Required resources in Greek"}}
  ],
  "video_recommendations": [
    {{"title": "Video title", "channel": "Channel name", "url": "https://www.youtube.com/watch?v=...", "duration": "MM:SS", "topic": "Video topic description", "relevance": "Why relevant to this business in Greek"}}
  ]
}}
```

**MANDATORY**: Use "number": 8 (not "section"), include EXACTLY 5 video_recommendations with all 6 fields (title, channel, url, duration, topic, relevance)."""

def get_section_9_prompt(section_num, company_info, relevant_files):
    return f"""Generate **Section 9: Leadership Development & Team Building** for Greek SME.

**CRITICAL**: Save your response as section_{section_num}_generated.json in the current working directory.

**Company**: {company_info.get('company_name', 'Greek SME')}
**Relevant Files**: {', '.join([f.name for f in relevant_files]) if relevant_files else 'Leadership assessment data'}

**Your Task**: Generate 800-1200 words on leadership:

**IMPORTANT - Language**: Think and analyze in English for clarity, but write ALL final output content in Greek. Technical terms may remain in English where appropriate (e.g., "DISC", "Myers-Briggs", "Big Five", "360 review").

1. **Content (HTML)**:
   - **Psychometric Profile**: Use Read tool to examine ALL images and PDFs. Look for personality tests, leadership assessments, evaluation reports with scores (base 100). Common tests: DISC, Myers-Briggs, Big Five, 360 reviews. Extract ALL numerical scores and interpret them.
   - Leadership style assessment based on findings
   - Team development strategies tailored to profile
   - Communication improvement plans
   - Conflict resolution guidance
   - Succession planning advice
   - Personal development roadmap with specific goals
   - Coaching recommendations

2. **KPIs** (3-5): Leadership scores (if found), team metrics, development targets

3. **Tables** (if applicable): Psychometric profile breakdown with scores

4. **Action Items** (4-5): Leadership coaching, team building, skill development, assessment follow-up

**CRITICAL - Output Format**: Return ONLY valid JSON with this EXACT structure:
```json
{{
  "number": 9,
  "title": "Leadership Development & Team Building",
  "content": "<div>HTML formatted content in Greek...</div>",
  "kpis": [
    {{"label": "KPI label in Greek", "value": "value with units"}}
  ],
  "tables": [
    {{"title": "Table title in Greek", "headers": ["Column 1", "Column 2", "..."], "rows": [["Cell 1,1", "Cell 1,2", "..."], ["Cell 2,1", "Cell 2,2", "..."]]}}
  ],
  "action_items": [
    {{"title": "Action title in Greek", "priority": "Υψηλή|Μέτρια|Χαμηλή", "timeline": "X μήνες", "description": "Detailed description in Greek", "expected_impact": "Expected results in Greek", "resources_needed": "Required resources in Greek"}}
  ]
}}
```

**MANDATORY**: Use "number": 9 (not "section"), use "label" for KPIs, use "title" for action_items."""

def get_section_10_prompt(section_num, company_info, relevant_files):
    return f"""Generate **Section 10: Implementation Roadmap & Success Metrics** for Greek SME.

**CRITICAL**: Save your response as section_{section_num}_generated.json in the current working directory.

**Company**: {company_info.get('company_name', 'Greek SME')}

**Context**: Synthesize action items from previous sections 1-9 into coherent implementation plan.

**Your Task**: Generate 800-1200 words implementation roadmap:

**IMPORTANT - Language**: Think and analyze in English for clarity, but write ALL final output content in Greek. Technical terms may remain in English where appropriate (e.g., "KPI", "ROI", "Gantt").

1. **Content (HTML)**:
   - Comprehensive 30-60-90 day action plans
   - Priority matrix (urgent/important framework)
   - Detailed implementation checklists
   - Success metrics and KPI frameworks
   - Milestone tracking systems
   - Resource allocation guidance (budget, time, personnel)
   - Dependency management
   - Risk mitigation during implementation
   - Follow-up and review schedules

2. **KPIs** (5-6): Completion rates, milestones achieved, ROI metrics

3. **Tables** (2):
   - 90-day implementation timeline (Gantt-style)
   - Success metrics dashboard

4. **Action Items** (4-5): Project management setup, milestone reviews, tracking systems

**CRITICAL - Output Format**: Return ONLY valid JSON with this EXACT structure:
```json
{{
  "number": 10,
  "title": "Implementation Roadmap & Success Metrics",
  "content": "<div>HTML formatted content in Greek...</div>",
  "kpis": [
    {{"label": "KPI label in Greek", "value": "value with units"}}
  ],
  "tables": [
    {{"title": "Table title in Greek", "headers": ["Column 1", "Column 2", "..."], "rows": [["Cell 1,1", "Cell 1,2", "..."], ["Cell 2,1", "Cell 2,2", "..."]]}}
  ],
  "action_items": [
    {{"title": "Action title in Greek", "priority": "Υψηλή|Μέτρια|Χαμηλή", "timeline": "X μήνες", "description": "Detailed description in Greek", "expected_impact": "Expected results in Greek", "resources_needed": "Required resources in Greek"}}
  ]
}}
```

**MANDATORY**: Use "number": 10 (not "section"), use "label" for KPIs, use "title" for action_items."""

def get_section_11_prompt(section_num, company_info, relevant_files):
    return f"""Generate **Section 11: Legal & Regulatory Compliance Framework** for Greek SME.

**CRITICAL**: Save your response as section_{section_num}_generated.json in the current working directory.

**Company**: {company_info.get('company_name', 'Greek SME')} (AFM: {company_info.get('afm', 'N/A')}, KAD: {company_info.get('kad', 'N/A')})
**Relevant Files**: {', '.join([f.name for f in relevant_files]) if relevant_files else 'Tax and legal documents'}

**Your Task**: Generate 800-1200 words on compliance:

**IMPORTANT - Language**: Think and analyze in English for clarity, but write ALL final output content in Greek. Technical terms may remain in English where appropriate (e.g., "GDPR", "ISO").

1. **Content (HTML)**:
   - Legal structure analysis (ΑΕ, ΕΠΕ, ΙΚΕ, ατομική επιχείρηση)
   - Tax compliance assessment (analyze E1, E3, ENFIA if available)
   - ΑΑΔΕ requirements and deadlines
   - ΕΦΚΑ obligations for this business type
   - Industry-specific regulatory requirements (based on KAD)
   - GDPR compliance checklist
   - Labor law compliance
   - Insurance requirements
   - Licensing and permits needed
   - Useful Greek government portal links

2. **KPIs** (3-5): Compliance score, outstanding obligations, risk level

3. **Tables** (2):
   - Compliance checklist by authority (ΑΑΔΕ, ΕΦΚΑ, ΓΕΜΗ, etc.)
   - Annual compliance calendar with deadlines

4. **Action Items** (4-6): Compliance audits, policy updates, filings

**IMPORTANT**: Always include ΑΑΔΕ portal (https://1521.aade.gr/) in recommendations.

**CRITICAL - Output Format**: Return ONLY valid JSON with this EXACT structure:
```json
{{
  "number": 11,
  "title": "Legal & Regulatory Compliance Framework",
  "content": "<div>HTML formatted content in Greek...</div>",
  "kpis": [
    {{"label": "KPI label in Greek", "value": "value with units"}}
  ],
  "tables": [
    {{"title": "Table title in Greek", "headers": ["Column 1", "Column 2", "..."], "rows": [["Cell 1,1", "Cell 1,2", "..."], ["Cell 2,1", "Cell 2,2", "..."]]}}
  ],
  "action_items": [
    {{"title": "Action title in Greek", "priority": "Υψηλή|Μέτρια|Χαμηλή", "timeline": "X μήνες", "description": "Detailed description in Greek", "expected_impact": "Expected results in Greek", "resources_needed": "Required resources in Greek"}}
  ]
}}
```

**MANDATORY**: Use "number": 11 (not "section"), use "label" for KPIs, use "title" for action_items."""
