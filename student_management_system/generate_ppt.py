#!/usr/bin/env python3
"""
Generates a polished 12-slide PowerPoint presentation (.pptx)
for the Serverless Student Management System on AWS Academy.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette
    DARK_BLUE = RGBColor(15, 23, 42)      # #0F172A Slate 900
    NAVY = RGBColor(30, 41, 59)           # #1E293B Slate 800
    INDIGO = RGBColor(79, 70, 229)        # #4F46E5 Indigo 600
    AWS_ORANGE = RGBColor(255, 153, 0)    # #FF9900 AWS Orange
    LIGHT_BG = RGBColor(248, 250, 252)    # #F8FAFC Slate 50
    CARD_BG = RGBColor(255, 255, 255)     # #FFFFFF Pure White
    TEXT_MAIN = RGBColor(30, 41, 59)      # #1E293B
    TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B
    BORDER_COLOR = RGBColor(226, 232, 240)# #E2E8F0
    EMERALD = RGBColor(16, 185, 129)      # #10B981

    blank_layout = prs.slide_layouts[6]

    def add_background(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category="STUDENT MANAGEMENT SYSTEM · AWS ACADEMY"):
        # Category tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(11.5), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = INDIGO
        
        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(28)
        p_title.font.bold = True
        p_title.font.color.rgb = DARK_BLUE

    def add_card(slide, left, top, width, height, title, items, badge=""):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = BORDER_COLOR
        card.line.width = Pt(1)

        tx_box = slide.shapes.add_textbox(left + Inches(0.3), top + Inches(0.25), width - Inches(0.6), height - Inches(0.5))
        tf = tx_box.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(18)
        p_t.font.bold = True
        p_t.font.color.rgb = DARK_BLUE

        if badge:
            p_badge = tf.add_paragraph()
            p_badge.text = badge
            p_badge.font.size = Pt(10)
            p_badge.font.bold = True
            p_badge.font.color.rgb = AWS_ORANGE

        for item in items:
            p = tf.add_paragraph()
            p.text = f"•  {item}"
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_MAIN
            p.space_before = Pt(8)

    # ==================== SLIDE 1: Title Slide ====================
    s1 = prs.slides.add_slide(blank_layout)
    add_background(s1, DARK_BLUE)

    # Accent glow banner
    banner = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.2), Inches(11.333), Inches(5.1))
    banner.fill.solid()
    banner.fill.fore_color.rgb = NAVY
    banner.line.color.rgb = INDIGO
    banner.line.width = Pt(1.5)

    tb = s1.shapes.add_textbox(Inches(1.5), Inches(1.8), Inches(10.333), Inches(3.8))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "CLOUD COMPUTING PROJECT"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = AWS_ORANGE

    p1 = tf.add_paragraph()
    p1.text = "Serverless Student Management System"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    p1.space_before = Pt(10)

    p2 = tf.add_paragraph()
    p2.text = "Built on AWS Cloud · 100% Free Tier · AWS Academy Ready"
    p2.font.size = Pt(18)
    p2.font.color.rgb = RGBColor(203, 213, 225)
    p2.space_before = Pt(8)

    p3 = tf.add_paragraph()
    p3.text = "Technology Stack: AWS Lambda (Python) · Amazon DynamoDB · Amazon API Gateway · Web Dashboard"
    p3.font.size = Pt(13)
    p3.font.color.rgb = RGBColor(148, 163, 184)
    p3.space_before = Pt(28)

    # ==================== SLIDE 2: Project Overview ====================
    s2 = prs.slides.add_slide(blank_layout)
    add_background(s2, LIGHT_BG)
    add_header(s2, "Project Overview & Problem Statement")

    add_card(s2, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0),
        "The Traditional Problem",
        [
            "Manual pen-and-paper student records are prone to loss and human errors.",
            "Traditional local software runs on single computers and cannot be accessed remotely.",
            "Legacy client-server systems require expensive 24/7 dedicated server hosting.",
            "High maintenance, vulnerability to hardware crashes, and zero elasticity."
        ]
    )

    add_card(s2, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0),
        "Our Cloud Solution",
        [
            "Centralized web portal accessible from any browser securely.",
            "Instant CRUD operations for student admission, grading, and course enrollment.",
            "100% Serverless Cloud Backend: No physical servers to manage or patch.",
            "Zero Idle Cost: Automatically scales down to $0.00 when not in use."
        ]
    )

    # ==================== SLIDE 3: Why Serverless & AWS Academy? ====================
    s3 = prs.slides.add_slide(blank_layout)
    add_background(s3, LIGHT_BG)
    add_header(s3, "Why Serverless Architecture & AWS Academy?")

    add_card(s3, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0),
        "What is Serverless?",
        [
            "Code executes only on-demand in response to user events.",
            "Zero servers running in the background.",
            "Automatic scaling from 1 student to 100,000+ without reconfiguration.",
            "High availability handled natively by AWS data centers."
        ]
    )

    add_card(s3, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0),
        "Zero-Cost Guarantee",
        [
            "Traditional EC2 virtual machines bill every hour 24/7.",
            "Our Serverless design incurs $0.00 when idle.",
            "DynamoDB provides 25 GB free storage forever.",
            "AWS Lambda gives 1,000,000 free function calls every month."
        ]
    )

    add_card(s3, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0),
        "AWS Academy Friendly",
        [
            "Pre-configured for AWS Academy Learner Lab environments.",
            "Utilizes the standard LabRole for smooth deployment.",
            "Operates safely inside the $100 student sandbox credit.",
            "100% compliant with university guidelines."
        ]
    )

    # ==================== SLIDE 4: System Architecture ====================
    s4 = prs.slides.add_slide(blank_layout)
    add_background(s4, LIGHT_BG)
    add_header(s4, "System Architecture: End-to-End Workflow")

    steps = [
        ("1. Web Client", "User interacts with modern web dashboard (HTML5 / Tailwind CSS).", Inches(0.8)),
        ("2. API Gateway", "Routes HTTPS REST calls (GET, POST, PUT, DELETE) with CORS enabled.", Inches(3.8)),
        ("3. AWS Lambda", "Python serverless code handles business logic, validation, and analytics.", Inches(6.8)),
        ("4. Amazon DynamoDB", "Ultra-fast NoSQL cloud database stores and indexes student records.", Inches(9.8))
    ]

    for title, desc, left in steps:
        add_card(s4, left, Inches(1.8), Inches(2.7), Inches(3.5), title, [desc])

    # Summary callout card at bottom
    add_card(s4, Inches(0.8), Inches(5.5), Inches(11.7), Inches(1.4),
        "Architecture Summary",
        ["Completely decoupled 3-tier cloud architecture: Presentation Layer ➔ Logic Layer ➔ Data Layer."]
    )

    # ==================== SLIDE 5: Core AWS Services ====================
    s5 = prs.slides.add_slide(blank_layout)
    add_background(s5, LIGHT_BG)
    add_header(s5, "Deep Dive: Core AWS Cloud Services")

    add_card(s5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(2.4),
        "AWS Lambda (Compute Engine)",
        [
            "Runs backend Python 3.11 code on event triggers.",
            "Handles routing, student validation, and GPA computations.",
            "Billed per millisecond; completely free during development."
        ]
    )

    add_card(s5, Inches(6.8), Inches(1.8), Inches(5.6), Inches(2.4),
        "Amazon DynamoDB (Database)",
        [
            "Fully managed, high-performance NoSQL database.",
            "Partition Key: student_id for single-digit millisecond lookups.",
            "Pay-Per-Request pricing model with 25 GB free tier."
        ]
    )

    add_card(s5, Inches(0.8), Inches(4.4), Inches(5.6), Inches(2.4),
        "Amazon API Gateway (REST API)",
        [
            "Manages public HTTPS endpoints for frontend communication.",
            "Built-in Cross-Origin Resource Sharing (CORS) security.",
            "Lightweight HTTP API (v2) format with 1M free requests."
        ]
    )

    add_card(s5, Inches(6.8), Inches(4.4), Inches(5.6), Inches(2.4),
        "Amazon CloudWatch (Monitoring)",
        [
            "Automatically captures live execution and error logs.",
            "Provides real-time visibility into Lambda invocations.",
            "Essential for demonstration and system debugging."
        ]
    )

    # ==================== SLIDE 6: Key Features of the System ====================
    s6 = prs.slides.add_slide(blank_layout)
    add_background(s6, LIGHT_BG)
    add_header(s6, "Key System Capabilities & Features")

    add_card(s6, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0),
        "Student CRUD Operations",
        [
            "Add New Student with ID, name, email, department, GPA, and courses.",
            "View Full Profile with enrolled subjects and status chips.",
            "Edit Records to update GPA, academic year, or phone.",
            "Delete Confirmation Modal to protect against accidental deletion."
        ]
    )

    add_card(s6, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0),
        "Search & Multi-Filtering",
        [
            "Instant Search across student names, IDs, and email addresses.",
            "Filter by Department (Computer Science, EE, ME, Data Science, etc.).",
            "Filter by Academic Status (Active, Graduated, Suspended).",
            "Real-time list updates without page reloads."
        ]
    )

    add_card(s6, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0),
        "Dual-Mode Flexibility",
        [
            "AWS Cloud Mode: Talks directly to live API Gateway & DynamoDB.",
            "Local / Demo Mode: Zero-dependency offline engine for instant demos.",
            "One-Click Data Seeder to prepopulate realistic records.",
            "CSV Export to download full class rosters into Excel."
        ]
    )

    # ==================== SLIDE 7: Analytics & Visualization ====================
    s7 = prs.slides.add_slide(blank_layout)
    add_background(s7, LIGHT_BG)
    add_header(s7, "Analytics Dashboard & Visualizations")

    add_card(s7, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0),
        "Real-Time KPI Cards",
        [
            "Total Students Enrolled: Dynamic count from DynamoDB.",
            "Active Students Count: Tracks currently enrolled students.",
            "Class Average GPA: Automatically computed across all records.",
            "AWS Cost Tracker: Visual indicator confirming 100% Free Tier status."
        ]
    )

    add_card(s7, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0),
        "Interactive Charts (Chart.js)",
        [
            "Department Breakdown Doughnut Chart: Shows student distribution across majors.",
            "Academic Status & Year Bar Chart: Displays progression from 1st Year to Graduated.",
            "Responsive and interactive animations on hover.",
            "Helps academic administrators make data-driven decisions."
        ]
    )

    # ==================== SLIDE 8: DynamoDB Data Design ====================
    s8 = prs.slides.add_slide(blank_layout)
    add_background(s8, LIGHT_BG)
    add_header(s8, "Database Design (Amazon DynamoDB)")

    add_card(s8, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0),
        "Why NoSQL for Student Systems?",
        [
            "Schema Flexibility: Students can have variable course lists without complex SQL joins.",
            "Predictable Performance: Single-digit millisecond latency regardless of table size.",
            "Zero Database Administration: No patching, index rebuilding, or storage provisioning.",
            "Always Free Tier: 25 GB capacity is permanently free on AWS."
        ]
    )

    add_card(s8, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0),
        "Table Schema & Attributes",
        [
            "Partition Key (Primary Key): student_id (e.g., 'STU-1001')",
            "Attributes: first_name, last_name, email, phone",
            "Academic Details: department, year, gpa (Numeric 0.00-4.00)",
            "Course Enrollment: courses (List of course titles)",
            "Audit Timestamps: created_at, updated_at (ISO 8601 UTC)"
        ]
    )

    # ==================== SLIDE 9: Infrastructure as Code ====================
    s9 = prs.slides.add_slide(blank_layout)
    add_background(s9, LIGHT_BG)
    add_header(s9, "Infrastructure as Code (AWS CloudFormation)")

    add_card(s9, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0),
        "What is CloudFormation?",
        [
            "Automates infrastructure deployment using declarative YAML templates.",
            "Eliminates human errors in configuring cloud services.",
            "Enables reproducible, version-controlled cloud environments.",
            "1-Click deployment directly from the AWS Console."
        ]
    )

    add_card(s9, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0),
        "AWS Academy Custom Template",
        [
            "Template: cloudformation_academy.yaml",
            "Uses AWS Academy pre-assigned 'LabRole' for zero permission friction.",
            "Deploys DynamoDB, Lambda, and API Gateway in ~60 seconds.",
            "Outputs the live API URL automatically upon completion."
        ]
    )

    # ==================== SLIDE 10: Cost & Free Tier Analysis ====================
    s10 = prs.slides.add_slide(blank_layout)
    add_background(s10, LIGHT_BG)
    add_header(s10, "AWS Free Tier & Cost Breakdown")

    add_card(s10, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0),
        "Service Quota vs Project Usage",
        [
            "AWS Lambda: 1,000,000 free requests/mo (Project uses ~500 calls).",
            "DynamoDB: 25 GB free storage (Project uses < 1 MB).",
            "API Gateway: 1,000,000 calls free (Project uses ~500 calls).",
            "CloudWatch Logs: 5 GB free ingestion (Project uses < 5 MB).",
            "Total Monthly Cloud Bill: Exactly $0.00."
        ]
    )

    add_card(s10, Inches(6.8), Inches(1.8), Inches(5.6), Inches(5.0),
        "Safe Deletion & Resource Teardown",
        [
            "Zero Idle Drain: No hourly charges when left running.",
            "One-Click Cleanup: Delete the CloudFormation stack in AWS Console to remove everything.",
            "Automated Python Cleanup Script: python3 aws/cleanup.py available.",
            "Peace of mind for students and academic institutions."
        ]
    )

    # ==================== SLIDE 11: Security & Cloud Best Practices ====================
    s11 = prs.slides.add_slide(blank_layout)
    add_background(s11, LIGHT_BG)
    add_header(s11, "Security & Cloud Best Practices")

    add_card(s11, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0),
        "IAM Principle of Least Privilege",
        [
            "Lambda role only granted access to the specific student table.",
            "Cannot access other databases or cloud resources.",
            "Follows enterprise AWS security benchmarks."
        ]
    )

    add_card(s11, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0),
        "CORS & API Security",
        [
            "Cross-Origin Resource Sharing configured on API Gateway.",
            "Explicit OPTIONS preflight handling.",
            "Encrypted HTTPS transmission for all client-to-cloud traffic."
        ]
    )

    add_card(s11, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0),
        "Input Validation & Sanitization",
        [
            "Strict JSON schema parsing in Python backend.",
            "GPA bounds validation (0.00 to 4.00).",
            "Duplicate student ID prevention before writing to DynamoDB."
        ]
    )

    # ==================== SLIDE 12: Conclusion & Future Scope ====================
    s12 = prs.slides.add_slide(blank_layout)
    add_background(s12, DARK_BLUE)

    banner12 = s12.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.2), Inches(11.333), Inches(5.1))
    banner12.fill.solid()
    banner12.fill.fore_color.rgb = NAVY
    banner12.line.color.rgb = INDIGO
    banner12.line.width = Pt(1.5)

    tb12 = s12.shapes.add_textbox(Inches(1.5), Inches(1.6), Inches(10.333), Inches(4.2))
    tf12 = tb12.text_frame
    tf12.word_wrap = True

    p_c0 = tf12.paragraphs[0]
    p_c0.text = "CONCLUSION & FUTURE ENHANCEMENTS"
    p_c0.font.size = Pt(14)
    p_c0.font.bold = True
    p_c0.font.color.rgb = AWS_ORANGE

    p_c1 = tf12.add_paragraph()
    p_c1.text = "Project Summary & What's Next"
    p_c1.font.size = Pt(28)
    p_c1.font.bold = True
    p_c1.font.color.rgb = RGBColor(255, 255, 255)
    p_c1.space_before = Pt(8)

    p_c2 = tf12.add_paragraph()
    p_c2.text = "• Successfully built a full-stack, 100% Free Tier serverless cloud application on AWS Academy."
    p_c2.font.size = Pt(13)
    p_c2.font.color.rgb = RGBColor(226, 232, 240)
    p_c2.space_before = Pt(14)

    p_c3 = tf12.add_paragraph()
    p_c3.text = "• Demonstrated Infrastructure-as-Code with 1-click CloudFormation automation."
    p_c3.font.size = Pt(13)
    p_c3.font.color.rgb = RGBColor(226, 232, 240)
    p_c3.space_before = Pt(8)

    p_c4 = tf12.add_paragraph()
    p_c4.text = "• Future Scope: Student photo uploads via Amazon S3, SMS/Email alerts via Amazon SNS, and Role-based Auth with Amazon Cognito."
    p_c4.font.size = Pt(13)
    p_c4.font.color.rgb = RGBColor(226, 232, 240)
    p_c4.space_before = Pt(8)

    p_c5 = tf12.add_paragraph()
    p_c5.text = "Thank You! Questions & Live Demonstration."
    p_c5.font.size = Pt(18)
    p_c5.font.bold = True
    p_c5.font.color.rgb = AWS_ORANGE
    p_c5.space_before = Pt(24)

    # Save presentation
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Student_Management_System_Presentation.pptx")
    prs.save(output_path)
    print(f"✅ Successfully generated PowerPoint presentation: {output_path}")

if __name__ == '__main__':
    create_deck()
