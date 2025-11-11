"""Example usage of the refactored CaseFactory with ConversationTurns for testing a meta agent that creates sales copilots for ADD*ONE."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.eval.case_factory import CaseFactory, create_tool_call_part

def example_addone_sales_copilot_creation():
    """Demonstrate test cases for ADD*ONE frontend developer creating a sales copilot for their website."""
    
    factory = CaseFactory()
    
    # Test case 1: ADD*ONE Sales Copilot Creation Request
    factory.create_simple_case(
        name="ADD*ONE Sales Copilot Creation",
        user_input="Ich möchte einen Copilot für die ADD*ONE Webseite erstellen. Der Copilot soll der perfekte Sales Assistant sein und potenziellen Kunden die Software schmackhaft machen.",
        expected_response="Perfekt! Ich erstelle einen Sales-Copiloten für die ADD*ONE Webseite. Dafür richte ich die AI Knowledge mit den relevanten Ressourcen ein und konfiguriere den Copiloten mit den passenden Plugins. Welche spezifischen Ressourcen haben Sie verfügbar?",
        description="Test für die initiale Sales-Copilot Erstellung für ADD*ONE",
        metadata={"category": "sales_copilot_creation", "complexity": "simple", "company": "addone"}
    )
    
    # Test case 2: Vollständige ADD*ONE Sales Copilot Konfiguration mit Ressourcen-Setup
    conversation = factory.create_conversation_turns()
    
    # Benutzer stellt eine detaillierte Anfrage
    conversation.add_user_message("Ich bin Frontendentwickler bei ADD*ONE und möchte einen Sales-Copiloten für unsere Webseite. Mir stehen folgende Ressourcen zur Verfügung: INFORM Webseite über KI-Systeme für Geschäftsprozesse und ein SharePoint Ordner mit AddOne-InfoPapers Broschüren.")
    conversation.add_model_message("Ausgezeichnet! Ich erstelle einen perfekten Sales-Copiloten für ADD*ONE. Lassen Sie mich zuerst eine Sammlung für Ihre Ressourcen erstellen und dann die entsprechenden Plugins konfigurieren.")
    
    # Erste Tool-Aufrufe: AI Knowledge Collection erstellen
    conversation.add_tool_call(
        tool_call_id="create_collection_1", 
        tool_name="create_collection", 
        args={
            "collection_name": "addone-sales-resources",
            "description": "Sammlung für ADD*ONE Sales-Materialien und Produktinformationen"
        }
    )
    conversation.add_tool_response(
        tool_call_id="create_collection_1", 
        tool_name="create_collection", 
        content="Collection 'addone-sales-resources' erfolgreich erstellt"
    )
    
    # Quellen zur Collection hinzufügen
    conversation.add_model_message("Perfekt! Jetzt füge ich die INFORM Webseite als erste Quelle hinzu.")
    conversation.add_tool_call(
        tool_call_id="create_source_1", 
        tool_name="create_source", 
        args={
            "collection_name": "addone-sales-resources",
            "source_name": "inform-website",
            "source_type": "web",
            "url": "https://www.inform-software.de/ki-systeme-geschaeftsprozesse",
            "description": "INFORM Webseite über KI-Systeme für die Optimierung von Geschäftsprozessen"
        }
    )
    conversation.add_tool_response(
        tool_call_id="create_source_1", 
        tool_name="create_source", 
        content="Quelle 'inform-website' erfolgreich zur Collection hinzugefügt"
    )
    
    # SharePoint Ordner als Quelle hinzufügen
    conversation.add_model_message("Jetzt konfiguriere ich den SharePoint Ordner mit den AddOne-InfoPapers.")
    conversation.add_tool_call(
        tool_call_id="create_source_2", 
        tool_name="create_source", 
        args={
            "collection_name": "addone-sales-resources",
            "source_name": "addone-infopapers",
            "source_type": "sharepoint",
            "path": "/sharepoint/AddOne-InfoPapers",
            "description": "SharePoint Ordner mit AddOne-InfoPapers Broschüren"
        }
    )
    conversation.add_tool_response(
        tool_call_id="create_source_2", 
        tool_name="create_source", 
        content="SharePoint Quelle 'addone-infopapers' erfolgreich konfiguriert"
    )
    
    # Sales-Copilot Endpoint erstellen
    conversation.add_model_message("Excellent! Alle Ressourcen sind konfiguriert. Jetzt erstelle ich den Sales-Copilot Endpoint mit optimalen Einstellungen.")
    conversation.add_tool_call(
        tool_call_id="create_endpoint_1", 
        tool_name="create_endpoint_api_createEndpoint_post", 
        args={
            "endpoint": "addone-sales-copilot", 
            "endpoint_attributes": {
                "dep_name": "gpt-4o", 
                "instructions": "Du bist der perfekte Sales Assistant für ADD*ONE. Deine Aufgabe ist es, potenzielle Kunden von unserer Software zu überzeugen. Nutze die verfügbaren Ressourcen über INFORM KI-Systeme und AddOne-InfoPapers, um professionelle und überzeugende Antworten zu geben. Sei enthusiastisch, aber authentisch.", 
                "default_message": "Hallo! Ich bin Ihr Sales Assistant für ADD*ONE. Wie kann ich Ihnen dabei helfen, die perfekte Software-Lösung für Ihr Unternehmen zu finden?"
            }
        }
    )
    conversation.add_tool_response(
        tool_call_id="create_endpoint_1", 
        tool_name="create_endpoint_api_createEndpoint_post", 
        content="ADD*ONE Sales-Copilot Endpoint erfolgreich erstellt"
    )
    
    # Copilot-Konfiguration setzen
    conversation.add_model_message("Jetzt verbinde ich den Copiloten mit den AI Knowledge Plugins und API Operations.")
    conversation.add_tool_call(
        tool_call_id="set_config_1", 
        tool_name="set_config_api_setConfig_post", 
        args={
            "endpoint": "addone-sales-copilot",
            "config": {
                "plugins": ["ai-knowledge-plugin", "api-operations"],
                "knowledge_collections": ["addone-sales-resources"],
                "response_style": "sales_optimized",
                "language": "german"
            }
        }
    )
    conversation.add_tool_response(
        tool_call_id="set_config_1", 
        tool_name="set_config_api_setConfig_post", 
        content="Copilot-Konfiguration erfolgreich gesetzt mit AI Knowledge Plugin und API Operations"
    )
    
    # Das Gespräch mit der finalen Antwort abschließen
    factory.create_conversation_case(
        name="ADD*ONE Sales Copilot - Vollständige Konfiguration",
        conversation_turns=conversation,
        expected_final_response="Perfekt! Ihr ADD*ONE Sales-Copilot ist vollständig konfiguriert und einsatzbereit. Der Copilot hat Zugriff auf die INFORM Webseite und Ihre AddOne-InfoPapers, ist mit dem AI Knowledge Plugin und API Operations ausgestattet und speziell für Sales-Gespräche optimiert. Sie können ihn jetzt auf Ihrer Webseite einsetzen!",
        description="Vollständige ADD*ONE Sales-Copilot Erstellung mit Ressourcen-Integration und Plugin-Konfiguration",
        metadata={"category": "sales_copilot", "complexity": "medium", "company": "addone", "tools_used": ["ai_knowledge", "ally_config"]}
    )
    
    # Test case 3: Erweiterte ADD*ONE Copilot-Konfiguration mit Iterationen
    conversation2 = factory.create_conversation_turns()
    
    # Benutzer möchte den Copiloten erweitern
    conversation2.add_user_message("Der Sales-Copilot ist super! Können Sie ihn noch erweitern? Ich hätte gerne zusätzliche Funktionen für Lead-Qualifizierung und eine Integration mit unserem CRM-System.")
    conversation2.add_model_message("Gerne erweitere ich Ihren ADD*ONE Sales-Copilot! Ich füge Lead-Qualifizierungs-Tools hinzu und konfiguriere CRM-Integrationen. Lassen Sie mich zuerst prüfen, welche zusätzlichen Ressourcen verfügbar sind.")
    
    # Verfügbare AI-Modelle prüfen
    conversation2.add_tool_call(
        tool_call_id="check_models_1", 
        tool_name="get_available_AI_models", 
        args={}
    )
    conversation2.add_tool_response(
        tool_call_id="check_models_1", 
        tool_name="get_available_AI_models", 
        content="Verfügbare Modelle: gpt-4o, gpt-4-turbo, claude-3-opus, gpt-4o-mini"
    )
    
    # Bestehende Collections überprüfen
    conversation2.add_model_message("Perfekt! Jetzt schaue ich, welche Collections bereits vorhanden sind.")
    conversation2.add_tool_call(
        tool_call_id="list_collections_2", 
        tool_name="list_collections", 
        args={}
    )
    conversation2.add_tool_response(
        tool_call_id="list_collections_2", 
        tool_name="list_collections", 
        content="Collections: addone-sales-resources, crm-data, lead-qualification-guides"
    )
    
    # Erweiterte Copilot-Konfiguration
    conversation2.add_model_message("Ausgezeichnet! Ich sehe, dass bereits CRM-Daten und Lead-Qualifizierungs-Guidelines verfügbar sind. Ich aktualisiere jetzt Ihren Copiloten.")
    
    # Aktualisierte Endpoint-Konfiguration
    conversation2.add_tool_call(
        tool_call_id="update_config_1", 
        tool_name="set_config_api_setConfig_post", 
        args={
            "endpoint": "addone-sales-copilot",
            "config": {
                "plugins": ["ai-knowledge-plugin", "api-operations", "crm-integration", "lead-scorer"],
                "knowledge_collections": ["addone-sales-resources", "crm-data", "lead-qualification-guides"],
                "response_style": "sales_optimized",
                "language": "german",
                "advanced_features": {
                    "lead_qualification": True,
                    "crm_integration": True,
                    "personalization": True
                }
            }
        }
    )
    conversation2.add_tool_response(
        tool_call_id="update_config_1", 
        tool_name="set_config_api_setConfig_post", 
        content="Erweiterte Copilot-Konfiguration mit CRM-Integration und Lead-Qualifizierung erfolgreich aktualisiert"
    )
    
    # Benutzer fragt nach Analytics
    conversation2.add_user_message("Das ist fantastisch! Können Sie auch Analytics einrichten, damit ich die Performance des Copiloten überwachen kann?")
    
    # Das Test-Case erstellen
    factory.create_conversation_case(
        name="ADD*ONE Sales Copilot - Erweiterte Features",
        conversation_turns=conversation2,
        expected_final_response="Selbstverständlich! Ich richte umfassende Analytics für Ihren ADD*ONE Sales-Copilot ein, damit Sie Lead-Konversionsraten, Benutzerinteraktionen und Sales-Performance in Echtzeit überwachen können.",
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="create_analytics_dashboard", 
                args={"endpoint": "addone-sales-copilot", "metrics": ["conversion_rate", "lead_quality", "interaction_time", "sales_funnel_progression"]},
                tool_call_id="setup_analytics_1"
            )
        ],
        description="Erweiterte ADD*ONE Sales-Copilot Konfiguration mit CRM-Integration, Lead-Qualifizierung und Analytics",
        metadata={"category": "enterprise_sales_copilot", "complexity": "high", "company": "addone", "tools_used": ["ally_config", "ai_knowledge", "crm_integration", "analytics"]}
    )
    
    # Test case 4: Validierungsbeispiel für ADD*ONE
    conversation3 = factory.create_conversation_turns()
    
    # Versuch, eine ungültige Unterhaltung zu erstellen (beginnt nicht mit Benutzer-Nachricht)
    conversation3.add_model_message("Ich starte die Unterhaltung falsch")
    
    # Validierung wird diesen Fehler abfangen
    try:
        factory.create_conversation_case(
            name="Ungültiger ADD*ONE Konversationstest",
            conversation_turns=conversation3,
            description="Dieser Test sollte bei der Validierung fehlschlagen"
        )
    except ValueError as e:
        print(f"Validierung hat erwarteten Fehler abgefangen: {e}")
    
    # Dataset erstellen
    dataset = factory.build_dataset("ADD*ONE Sales Copilot Test Suite")
    
    print(f"ADD*ONE Sales-Copilot Test-Dataset erstellt mit {len(dataset.cases)} Test-Fällen:")
    for case in dataset.cases:
        print(f"  - {case.name}")
    
    return dataset

def example_addone_conversation_validation():
    """Demonstriere Konversations-Validierungsfunktionen für ADD*ONE Use Cases."""
    
    factory = CaseFactory()
    
    # Beispiel 1: Gültige ADD*ONE Konversation
    valid_conversation = factory.create_conversation_turns()
    valid_conversation.add_user_message("Hallo, ich brauche einen Sales-Copiloten für ADD*ONE")
    valid_conversation.add_model_message("Gerne helfe ich Ihnen dabei!")
    valid_conversation.add_user_message("Wie können Sie mir dabei helfen?")
    
    errors = valid_conversation.validate()
    print(f"Gültige ADD*ONE Konversation Fehler: {errors}")  # Sollte leer sein
    
    # Beispiel 2: Ungültige Konversation - endet nicht mit Benutzer-Anfrage
    invalid_conversation = factory.create_conversation_turns()
    invalid_conversation.add_user_message("Hallo")
    invalid_conversation.add_model_message("Hi! Wie kann ich helfen?")
    # Fehlende finale Benutzer-Nachricht
    
    errors = invalid_conversation.validate()
    print(f"Ungültige ADD*ONE Konversation Fehler: {errors}")  # Sollte Validierungsfehler zeigen
    
    # Beispiel 3: Tool-Aufruf ohne Antwort
    incomplete_conversation = factory.create_conversation_turns()
    incomplete_conversation.add_user_message("Erstellen Sie eine Collection für ADD*ONE")
    incomplete_conversation.add_tool_call("call_1", "create_collection", {"collection_name": "addone-test"})
    # Fehlende Tool-Antwort
    
    errors = incomplete_conversation.validate()
    print(f"Unvollständige ADD*ONE Konversation Fehler: {errors}")  # Sollte Tool-Aufruf-Fehler zeigen


if __name__ == "__main__":
    # Führe die angepassten ADD*ONE Beispiele aus
    dataset = example_addone_sales_copilot_creation()
    
    # Demonstriere Validierung
    print("\n--- ADD*ONE Validierungsbeispiele ---")
    example_addone_conversation_validation()
