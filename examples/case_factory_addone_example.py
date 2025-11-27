"""Example usage of the refactored CaseFactory with ConversationTurns for testing a meta agent that creates sales copilots for ADD*ONE."""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.eval.case_factory import CaseFactory, create_tool_call_part

def example_addone_sales_copilot_creation():
    """Demonstrate test cases for ADD*ONE frontend developer creating a sales copilot for their website."""
    
    factory = CaseFactory()
    
    # Verwende eine einzige ConversationTurns Instanz für alle Phasen
    convo = factory.create_conversation_turns()

    # Case 1: Initiale Anfrage - Agent fragt nach Geschäftsbereich und Projektnummer
    convo.add_user_message(
        "Ich möchte einen Copilot für die ADD*ONE Webseite erstellen. Der Copilot soll der perfekte Sales Assistant sein und potenziellen Kunden die Software schmackhaft machen."
    )
    case1_expected = "Perfekt! Ich erstelle einen Sales-Copiloten für die ADD*ONE Webseite. Dafür richte ich AI Knowledge mit relevanten Ressourcen ein und konfiguriere den Copiloten. Bevor wir starten: In welchem Geschäftsbereich arbeiten Sie und wie lautet Ihre Projektnummer? (z.B. GB10 mit Projektnummer 80000)"
    factory.create_conversation_case(
        name="ADD*ONE Sales Copilot – Initiale Anfrage",
        conversation_turns=convo,
        expected_final_response=case1_expected,
        description="Erste Nutzeranfrage zur Erstellung eines Sales Copiloten"
    )

    # Füge erwartete Antwort als ModelResponse hinzu, um Gespräch fortzusetzen
    convo.add_model_message(case1_expected)

    # Case 2: Nutzer gibt Geschäftsbereich und Projektnummer an, Agent speichert beide und fragt nach Links
    convo.add_user_message(
        "Ich arbeite im Geschäftsbereich GB10 und die Projektnummer ist 80000. Wir haben eine INFORM Webseite über KI-Systeme und einen SharePoint Ordner mit AddOne-InfoPapers, ich suche gerade die Links heraus."
    )
    case2_expected = "Super! Ich habe notiert, dass Sie im Geschäftsbereich GB10 mit der Projektnummer 80000 arbeiten. Bitte senden Sie mir beide Links (INFORM Webseite und SharePoint). Sobald ich beide habe, erstelle ich die Collection und füge die Quellen hinzu."
    factory.create_conversation_case(
        name="ADD*ONE Sales Copilot – Geschäftsbereich & Projektnummer gespeichert & Link-Anfrage",
        conversation_turns=convo,
        expected_final_response=case2_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="set_geschaeftsbereich",
                args={"geschaeftsbereich": "GB10"},
                tool_call_id="set_geschaeftsbereich_1"
            ),
            create_tool_call_part(
                tool_name="set_project_number",
                args={"project_number": "80000"},
                tool_call_id="set_project_number_1"
            )
        ],
        description="Agent speichert Geschäftsbereich und Projektnummer und fordert konkrete Links für strukturierte Quellenanlage"
    )

    convo.add_tool_call(
        tool_call_id="set_geschaeftsbereich_1",
        tool_name="set_geschaeftsbereich",
        args={"geschaeftsbereich": "GB10"}
    )
    convo.add_tool_response(
        tool_call_id="set_geschaeftsbereich_1",
        tool_name="set_geschaeftsbereich",
        content="Business area set to: GB10"
    )
    convo.add_tool_call(
        tool_call_id="set_project_number_1",
        tool_name="set_project_number",
        args={"project_number": "80000"}
    )
    convo.add_tool_response(
        tool_call_id="set_project_number_1",
        tool_name="set_project_number",
        content="Project number set to: 80000"
    )
    convo.add_model_message(case2_expected)

    # Case 3: Nutzer liefert Webseiten-Link -> wird notiert
    convo.add_user_message(
        "INFORM Webseite Link: https://www.inform-software.com/de"
    )
    case3_expected = "Perfekt, die INFORM Webseite ist notiert. Bitte senden Sie jetzt noch den SharePoint/OneDrive Link zu den AddOne-InfoPapers."
    factory.create_conversation_case(
        name="ADD*ONE Sales Copilot – Webseite Link erhalten",
        conversation_turns=convo,
        expected_final_response=case3_expected,
        description="Erste Quelle (Website) wird vom Agenten notiert"
    )
    convo.add_model_message(case3_expected)

    # Case 4: Nutzer liefert SharePoint Link -> beide Sources + Collection werden erstellt
    convo.add_user_message(
        "SharePoint Link: https://informsoftwaregmbh-my.sharepoint.com/:f:/g/personal/johannes_schillberg_inform-software_com/Erci0wuz2RVEinJQ7drbjT0BwpIOSmGNuDqyiQ9FJax5xA?e=WGtgpM"
    )
    case4_expected = "Alle Quellen sind jetzt konfiguriert. Soll ich den Endpoint für den Sales-Copiloten erstellen?"
    factory.create_conversation_case(
        name="ADD*ONE Sales Copilot – Collection mit beiden Quellen erstellt",
        conversation_turns=convo,
        expected_final_response=case4_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="create_source",
                args={
                    "source_name": "inform_website",
                    "source_type": "web",
                    "url": "https://www.inform-software.com/de",
                    "description": "INFORM Webseite über KI-Systeme & Optimierung von Geschäftsprozessen"
                },
                tool_call_id="create_source_website_1"
            ),
            create_tool_call_part(
                tool_name="create_source",
                args={
                    "source_name": "addone_infopapers",
                    "source_type": "sharepoint",
                    "path": "https://informsoftwaregmbh-my.sharepoint.com/:f:/g/personal/johannes_schillberg_inform-software_com/Erci0wuz2RVEinJQ7drbjT0BwpIOSmGNuDqyiQ9FJax5xA?e=WGtgpM",
                    "description": "SharePoint Ordner mit AddOne-InfoPapers Broschüren"
                },
                tool_call_id="create_source_sharepoint_1"
            ),
            create_tool_call_part(
                tool_name="create_collection",
                args={
                    "collection_name": "addone_sales_resources",
                    "description": "Sales-relevante Ressourcen & Produktinfos für ADD*ONE",
                    "source_names": ["inform_website", "addone_infopapers"]
                },
                tool_call_id="create_collection_1"
            )
        ],
        description="Beide Sources werden erstellt, dann Collection mit beiden Sources angelegt"
    )
    # Füge die erwarteten Tool-Aktionen zur Konversation hinzu
    convo.add_model_message("Ich erstelle jetzt beide Quellen und dann die Collection.")
    convo.add_tool_call(
        tool_call_id="create_source_website_1",
        tool_name="create_source",
        args={
            "source_name": "inform_website",
            "source_type": "web",
            "url": "https://www.inform-software.com/de",
            "description": "INFORM Webseite über KI-Systeme & Optimierung von Geschäftsprozessen"
        }
    )
    convo.add_tool_response(
        tool_call_id="create_source_website_1",
        tool_name="create_source",
        content="Quelle 'inform_website' erstellt"
    )
    convo.add_model_message("Website-Quelle erstellt. Jetzt die SharePoint-Quelle.")
    convo.add_tool_call(
        tool_call_id="create_source_sharepoint_1",
        tool_name="create_source",
        args={
            "source_name": "addone_infopapers",
            "source_type": "sharepoint",
            "path": "https://informsoftwaregmbh-my.sharepoint.com/:f:/g/personal/johannes_schillberg_inform-software_com/Erci0wuz2RVEinJQ7drbjT0BwpIOSmGNuDqyiQ9FJax5xA?e=WGtgpM",
            "description": "SharePoint Ordner mit AddOne-InfoPapers Broschüren"
        }
    )
    convo.add_tool_response(
        tool_call_id="create_source_sharepoint_1",
        tool_name="create_source",
        content="Quelle 'addone_infopapers' erstellt"
    )
    convo.add_model_message("Beide Quellen erstellt. Jetzt lege ich die Collection mit beiden Quellen an.")
    convo.add_tool_call(
        tool_call_id="create_collection_1",
        tool_name="create_collection",
        args={
            "collection_name": "addone_sales_resources",
            "description": "Sales-relevante Ressourcen & Produktinfos für ADD*ONE",
            "source_names": ["inform_website", "addone_infopapers"]
        }
    )
    convo.add_tool_response(
        tool_call_id="create_collection_1",
        tool_name="create_collection",
        content="Collection 'addone_sales_resources' mit beiden Quellen erstellt"
    )
    convo.add_model_message(case4_expected)

    # Case 5: Nutzer bestätigt Endpoint Erstellung -> Modellabfrage + Endpoint (mit endpoint_name speichern)
    convo.add_user_message("Ja, bitte erstellen Sie jetzt den Sales-Copilot Endpoint.")
    case5_expected = "Der Endpoint 'addone_sales_copilot' ist bereit. Möchten Sie, dass ich die konfigurierten Quellen zur Verifikation aufliste?"
    factory.create_conversation_case(
        name="ADD*ONE Sales Copilot – Endpoint erstellt & gespeichert",
        conversation_turns=convo,
        expected_final_response=case5_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="get_available_AI_models_api_getAvailableAIModels_post",
                args={},
                tool_call_id="check_models_1"
            ),
            create_tool_call_part(
                tool_name="create_endpoint_api_createEndpoint_post",
                args={
                    "endpoint": "/gb10/addone_sales_copilot",
                    "endpoint_attributes": {
                        "dep_name": "gpt-4o",
                        "instructions": "Du bist der Sales Assistant für ADD*ONE. Nutze die Quellen (INFORM Webseite, AddOne InfoPapers) für überzeugende Antworten.",
                        "default_message": "Hallo! Ich bin Ihr ADD*ONE Sales Assistant. Womit kann ich helfen?"
                    }
                },
                tool_call_id="create_endpoint_1"
            ),
            create_tool_call_part(
                tool_name="set_endpoint_name",
                args={"endpoint_name": "/gb10/addone_sales_copilot"},
                tool_call_id="set_endpoint_name_1"
            )
        ],
        description="Endpoint nach Modellauswahl erstellt und endpoint_name im Kontext gespeichert"
    )
    convo.add_tool_call(
        tool_call_id="check_models_1",
        tool_name="get_available_AI_models_api_getAvailableAIModels_post",
        args={}
    )
    convo.add_tool_response(
        tool_call_id="check_models_1",
        tool_name="get_available_AI_models_api_getAvailableAIModels_post",
        content="Verfügbare Modelle: gpt-4o, gpt-4-turbo, claude-3-opus, gpt-4o-mini"
    )
    convo.add_model_message("Ich verwende gpt-4o und erstelle den Endpoint.")
    convo.add_tool_call(
        tool_call_id="create_endpoint_1",
        tool_name="create_endpoint_api_createEndpoint_post",
        args={
            "endpoint": "/gb10/addone_sales_copilot",
            "endpoint_attributes": {
                "dep_name": "gpt-4o",
                "instructions": "Du bist der Sales Assistant für ADD*ONE. Nutze die Quellen (INFORM Webseite, AddOne InfoPapers) für überzeugende Antworten.",
                "default_message": "Hallo! Ich bin Ihr ADD*ONE Sales Assistant. Womit kann ich helfen?"
            }
        }
    )
    convo.add_tool_response(
        tool_call_id="create_endpoint_1",
        tool_name="create_endpoint_api_createEndpoint_post",
        content="Endpoint 'addone_sales_copilot' erstellt"
    )
    convo.add_tool_call(
        tool_call_id="set_endpoint_name_1",
        tool_name="set_endpoint_name",
        args={"endpoint_name": "/gb10/addone_sales_copilot"}
    )
    convo.add_tool_response(
        tool_call_id="set_endpoint_name_1",
        tool_name="set_endpoint_name",
        content="Endpoint name set to: /gb10/addone_sales_copilot"
    )
    convo.add_model_message(case5_expected)

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
    incomplete_conversation.add_tool_call("call_1", "create_collection", {"collection_name": "addone_test"})
    # Fehlende Tool-Antwort
    
    errors = incomplete_conversation.validate()
    print(f"Unvollständige ADD*ONE Konversation Fehler: {errors}")  # Sollte Tool-Aufruf-Fehler zeigen


if __name__ == "__main__":
    # Führe die angepassten ADD*ONE Beispiele aus
    dataset = example_addone_sales_copilot_creation()

    case_1=dataset.cases[0]
    from src.eval.case_factory import create_case_variant
    from src.eval.case_factory import MessageHistoryCase
    from src.util.case_visualization import visualize_single_case
    
    print("\n--- Beispiel Fall 1 ---")
    print(f"Name: {case_1.name}")
    message_history_case=MessageHistoryCase.from_case(case_1)
    
    # Visualize the first case
    print("\n=== Visualizing Case 1 ===")
    visualize_single_case(message_history_case)
        
    case_2=dataset.cases[1]
    print("\n--- Beispiel Fall 2 ---")
    print(f"Name: {case_2.name}")
    message_history_case_2=MessageHistoryCase.from_case(case_2)

    print("\n=== Visualizing Case 2 (with expected tool calls) ===")
    visualize_single_case(message_history_case_2)

    last_case=dataset.cases[-1]

    print("\n -- Komplette Konversation -- ")
    print(f"Name: {last_case.name}")
    message_history_case_last=MessageHistoryCase.from_case(last_case)
    print("\n=== Visualizing Last Case ===")
    visualize_single_case(message_history_case_last)


    # Demonstriere Validierung
    print("\n--- ADD*ONE Validierungsbeispiele ---")
    example_addone_conversation_validation()
