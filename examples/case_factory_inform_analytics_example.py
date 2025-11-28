"""Example usage of the refactored CaseFactory with ConversationTurns for testing a meta agent that helps analyze copilot metrics for Corporate AI Team."""

from meta_ally.eval.case_factory import CaseFactory, create_tool_call_part

def example_inform_copilot_analytics():
    """Demonstrate test cases for Corporate AI Team member analyzing the INFORM website copilot metrics."""
    
    factory = CaseFactory()
    
    # Verwende eine einzige ConversationTurns Instanz für alle Phasen
    convo = factory.create_conversation_turns()

    # Case 1: Initiale Anfrage zu Metriken
    convo.add_user_message(
        "Ich betreue den Copilot auf der INFORM Webseite. Ich würde gerne wissen, wie oft der Chatbot genutzt wurde, wie zufrieden die Nutzer sind, wie groß die Kosten sind, und wie man einfach Kosten sparen könnte."
    )
    case1_expected = "Verstanden! Ich helfe Ihnen gerne bei der Analyse des INFORM Webseiten-Copilots. Ich werde für Sie die Session-Historien, Nutzerbewertungen und Kosten der letzten 30 Tage abrufen. Anschließend kann ich Ihnen auch günstigere Modellalternativen vorschlagen. Einen Moment bitte."
    factory.create_conversation_case(
        name="INFORM Copilot Analytics – Initiale Anfrage",
        conversation_turns=convo,
        expected_final_response=case1_expected,
        description="Nutzer möchte umfassende Metriken zum INFORM Webseiten-Copilot",
        metadata={"phase": "initial", "endpoint": "gb80/inform_webseite_dummy", "company": "inform"}
    )
    # Füge erwartete Antwort als ModelResponse hinzu, um Gespräch fortzusetzen
    convo.add_model_message(case1_expected)

    # Case 2: Agent ruft Session Histories ab
    convo.add_user_message(
        "Ja, bitte zeigen Sie mir die Metriken."
    )
    case2_expected = "Die Session-Daten werden abgerufen. Ich hole jetzt auch die Bewertungen und Kosteninformationen."
    factory.create_conversation_case(
        name="INFORM Copilot Analytics – Session Histories Abruf",
        conversation_turns=convo,
        expected_final_response=case2_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="get_session_histories_api_getSessionHistories_post",
                args={
                    "endpoint": "/gb80/inform_webseite_dummy",
                    "days": 30
                },
                tool_call_id="get_sessions_1"
            )
        ],
        metadata={"phase": "session_retrieval", "endpoint": "gb80/inform_webseite_dummy", "tools_used": ["get_session_histories_api_getSessionHistories_post"]},
        description="Abruf der Session-Historien der letzten 30 Tage"
    )
    convo.add_model_message("Ich rufe die Session-Historien ab.")
    convo.add_tool_call(
        tool_call_id="get_sessions_1",
        tool_name="get_session_histories_api_getSessionHistories_post",
        args={
            "endpoint": "/gb80/inform_webseite_dummy",
            "days": 30
        }
    )
    convo.add_tool_response(
        tool_call_id="get_sessions_1",
        tool_name="get_session_histories_api_getSessionHistories_post",
        content="*[Echte Session History Daten vom API]*"
    )
    convo.add_model_message(case2_expected)

    # Case 3: Agent ruft Bewertungen und Kosten ab
    convo.add_user_message(
        "Weiter bitte."
    )
    case3_expected = "Ich habe alle Daten abgerufen. Lassen Sie mich diese für Sie zusammenfassen."
    factory.create_conversation_case(
        name="INFORM Copilot Analytics – Bewertungen und Kosten Abruf",
        conversation_turns=convo,
        expected_final_response=case3_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="get_ratings_aws_api_getRatingsAWS_post",
                args={
                    "endpoint": "/gb80/inform_webseite_dummy",
                    "days": 30
                },
                tool_call_id="get_ratings_1"
            ),
            create_tool_call_part(
                tool_name="get_cost_per_day_api_getCostPerDay_post",
                args={
                    "endpoint": "/gb80/inform_webseite_dummy",
                    "days": 30
                },
                tool_call_id="get_costs_1"
            )
        ],
        metadata={"phase": "ratings_costs_retrieval", "endpoint": "gb80/inform_webseite_dummy", "tools_used": ["get_ratings_aws_api_getRatingsAWS_post", "get_cost_per_day_api_getCostPerDay_post"]},
        description="Abruf der Nutzerbewertungen und Kosten pro Tag"
    )
    convo.add_model_message("Ich rufe jetzt die Bewertungen und Kosten ab.")
    convo.add_tool_call(
        tool_call_id="get_ratings_1",
        tool_name="get_ratings_aws_api_getRatingsAWS_post",
        args={
            "endpoint": "/gb80/inform_webseite_dummy",
            "days": 30
        }
    )
    convo.add_tool_response(
        tool_call_id="get_ratings_1",
        tool_name="get_ratings_aws_api_getRatingsAWS_post",
        content="*[Echte Rating Daten vom API]*"
    )
    convo.add_tool_call(
        tool_call_id="get_costs_1",
        tool_name="get_cost_per_day_api_getCostPerDay_post",
        args={
            "endpoint": "/gb80/inform_webseite_dummy",
            "days": 30
        }
    )
    convo.add_tool_response(
        tool_call_id="get_costs_1",
        tool_name="get_cost_per_day_api_getCostPerDay_post",
        content="*[Echte Kosten Daten vom API]*"
    )
    convo.add_model_message(case3_expected)

    # Case 4: Agent fasst Metriken zusammen
    convo.add_user_message(
        "Was bedeuten diese Zahlen für mich?"
    )
    case4_expected = """Hier ist die Zusammenfassung für Ihren INFORM Webseiten-Copilot:

**Nutzung (30 Tage):**
*[Hier echte Daten aus get_session_histories einfügen]*

**Nutzerzufriedenheit:**
*[Hier echte Daten aus get_ratings_aws einfügen]*

**Kosten:**
*[Hier echte Daten aus get_cost_per_day einfügen]*

**Einsparpotenzial:**
Möchten Sie, dass ich Ihnen günstigere Modellalternativen vorschlage? Mit einem kostengünstigeren Modell wie gpt-4o-mini könnten Sie die Kosten um bis zu 60-70% reduzieren, bei ähnlicher Qualität für Webseiten-Support-Anfragen."""
    factory.create_conversation_case(
        name="INFORM Copilot Analytics – Metriken Zusammenfassung",
        conversation_turns=convo,
        expected_final_response=case4_expected,
        metadata={"phase": "summary", "endpoint": "gb80/inform_webseite_dummy"},
        description="Agent fasst alle Metriken verständlich zusammen"
    )
    convo.add_model_message(case4_expected)

    # Case 5: Nutzer fragt nach Kostenoptimierung
    convo.add_user_message(
        "Ja, welche günstigeren Modelle würden Sie empfehlen?"
    )
    case5_expected = """Ich empfehle folgende Modellalternativen zur Kostenoptimierung:

*[Hier Liste verfügbarer günstigerer Modelle mit Kostenvergleich basierend auf aktuellen Kosten und verfügbaren Modellen]*

**Meine Empfehlung:** *[Konkrete Empfehlung basierend auf Use Case und Kostenanalyse]*

Soll ich ein Test-Setup mit einem günstigeren Modell für Sie vorbereiten?"""
    factory.create_conversation_case(
        name="INFORM Copilot Analytics – Modellempfehlungen",
        conversation_turns=convo,
        expected_final_response=case5_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="get_available_AI_models_api_getAvailableAIModels_post",
                args={},
                tool_call_id="get_models_1"
            )
        ],
        metadata={"phase": "cost_optimization", "endpoint": "gb80/inform_webseite_dummy", "tools_used": ["get_available_AI_models_api_getAvailableAIModels_post"]},
        description="Agent schlägt günstigere Modelle mit konkreten Einsparpotentialen vor"
    )
    convo.add_model_message("Ich prüfe die verfügbaren Modelle und deren Kostenstrukturen.")
    convo.add_tool_call(
        tool_call_id="get_models_1",
        tool_name="get_available_AI_models_api_getAvailableAIModels_post",
        args={}
    )
    convo.add_tool_response(
        tool_call_id="get_models_1",
        tool_name="get_available_AI_models_api_getAvailableAIModels_post",
        content="*[Verfügbare Modelle vom API]*"
    )
    convo.add_model_message(case5_expected)

    # Case 6: Nutzer möchte Details zu einem spezifischen Modell
    convo.add_user_message(
        "Das klingt gut. Können Sie mir mehr Details zu gpt-4o-mini geben und wie ich das umstellen kann?"
    )
    case6_expected = """**Modell-Details:**

*[Hier technische Details und Specs des empfohlenen Modells]*

**Für Ihren Use Case (INFORM Webseite):**
*[Hier Eignung für spezifischen Use Case]*

**Umstellung:**
Ich kann die Endpoint-Konfiguration für Sie anpassen:
1. Modell umstellen
2. Bestehende Knowledge-Quellen bleiben unverändert
3. System-Prompts bleiben gleich
4. Sofortige Kosteneinsparung

**Nächster Schritt:**
Soll ich die Umstellung jetzt durchführen? Sie können jederzeit zurückwechseln, falls Sie mit der Qualität nicht zufrieden sind."""
    factory.create_conversation_case(
        name="INFORM Copilot Analytics – Modell-Details & Umstellung",
        conversation_turns=convo,
        expected_final_response=case6_expected,
        metadata={"phase": "model_details", "endpoint": "gb80/inform_webseite_dummy", "suggested_model": "gpt-4o-mini"},
        description="Agent liefert detaillierte Informationen und Umstellungsprozess"
    )
    convo.add_model_message(case6_expected)

    # Fehlerfall zum Abschluss (separate fehlerhafte Konversation)
    invalid_convo = factory.create_conversation_turns()
    invalid_convo.add_model_message("Ich starte die Analytics-Unterhaltung falsch")
    try:
        factory.create_conversation_case(
            name="Ungültiger INFORM Analytics Konversationstest",
            conversation_turns=invalid_convo,
            description="Dieser Test sollte bei der Validierung fehlschlagen"
        )
    except ValueError as e:
        print(f"Validierung hat erwarteten Fehler abgefangen: {e}")
    
    # Dataset erstellen
    dataset = factory.build_dataset("INFORM Copilot Analytics Test Suite")
    
    print(f"\nINFORM Copilot Analytics Test-Dataset erstellt mit {len(dataset.cases)} Test-Fällen:")
    for case in dataset.cases:
        print(f"  - {case.name}")
    
    return dataset

def example_inform_analytics_validation():
    """Demonstriere Konversations-Validierungsfunktionen für INFORM Analytics Use Cases."""
    
    factory = CaseFactory()
    
    # Beispiel 1: Gültige INFORM Analytics Konversation
    valid_conversation = factory.create_conversation_turns()
    valid_conversation.add_user_message("Zeigen Sie mir die Metriken für den INFORM Copilot")
    valid_conversation.add_model_message("Gerne! Ich rufe die Daten ab.")
    valid_conversation.add_user_message("Wie sind die Kosten?")
    
    errors = valid_conversation.validate()
    print(f"Gültige INFORM Analytics Konversation Fehler: {errors}")  # Sollte leer sein
    
    # Beispiel 2: Ungültige Konversation - endet nicht mit Benutzer-Anfrage
    invalid_conversation = factory.create_conversation_turns()
    invalid_conversation.add_user_message("Hallo")
    invalid_conversation.add_model_message("Hi! Wie kann ich helfen?")
    # Fehlende finale Benutzer-Nachricht
    
    errors = invalid_conversation.validate()
    print(f"Ungültige INFORM Analytics Konversation Fehler: {errors}")  # Sollte Validierungsfehler zeigen
    
    # Beispiel 3: Tool-Aufruf ohne Antwort
    incomplete_conversation = factory.create_conversation_turns()
    incomplete_conversation.add_user_message("Zeigen Sie die Session Histories")
    incomplete_conversation.add_tool_call("call_1", "get_session_histories_api_getSessionHistories_post", {"endpoint": "/gb80/inform_webseite_dummy", "days": 30})
    # Fehlende Tool-Antwort
    
    errors = incomplete_conversation.validate()
    print(f"Unvollständige INFORM Analytics Konversation Fehler: {errors}")  # Sollte Tool-Aufruf-Fehler zeigen


if __name__ == "__main__":
    # Führe die INFORM Analytics Beispiele aus
    dataset = example_inform_copilot_analytics()
    
    # Demonstriere Validierung
    print("\n--- INFORM Analytics Validierungsbeispiele ---")
    example_inform_analytics_validation()
