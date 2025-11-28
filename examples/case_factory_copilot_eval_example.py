"""Example usage of the refactored CaseFactory with ConversationTurns for testing a meta agent that helps Corporate AI Team test copilot quality using Ally's Eval Tools."""

from meta_ally.eval.case_factory import CaseFactory, create_tool_call_part

def example_inform_copilot_quality_testing():
    """Demonstrate test cases for Corporate AI Team member testing quality of INFORM website copilot using Ally's evaluation tools."""
    
    factory = CaseFactory()
    
    # Verwende eine einzige ConversationTurns Instanz für alle Phasen
    convo = factory.create_conversation_turns()

    # Case 1: Initiale Anfrage zur Qualitätstestung
    convo.add_user_message(
        "Ich betreue den Copilot auf der INFORM Webseite und möchte die Qualität des Copiloten testen. Welche Möglichkeiten gibt es dafür?"
    )
    case1_expected = "Perfekt! Ich kann Ihnen helfen, die Qualität Ihres INFORM Webseiten-Copiloten mit Ally's Evaluation Tools zu testen. Ich werde zunächst prüfen, ob bereits Evaluierungs-Suites für diesen Copiloten existieren, oder wir können eine neue Testsuite erstellen. Soll ich die vorhandenen Testsuites abrufen?"
    factory.create_conversation_case(
        name="INFORM Copilot Quality Testing – Initiale Anfrage",
        conversation_turns=convo,
        expected_final_response=case1_expected,
        description="Corporate AI Team Mitglied möchte Copilot-Qualität testen",
        metadata={"phase": "initial", "endpoint": "gb80/inform_webseite_dummy", "company": "inform"}
    )
    # Füge erwartete Antwort als ModelResponse hinzu, um Gespräch fortzusetzen
    convo.add_model_message(case1_expected)

    # Case 2: Agent ruft existierende Evaluation Suites ab
    convo.add_user_message(
        "Ja, bitte zeigen Sie mir zunächst, welche Testsuites bereits existieren."
    )
    case2_expected = "Ich rufe die vorhandenen Evaluierungs-Suites ab. Basierend auf den Ergebnissen kann ich Ihnen eine bestehende Suite vorschlagen oder wir erstellen eine neue, maßgeschneiderte Testsuite."
    factory.create_conversation_case(
        name="INFORM Copilot Quality Testing – Abruf existierender Testsuites",
        conversation_turns=convo,
        expected_final_response=case2_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="get_evaluation_suites_api_getEvaluationSuites_post",
                args={
                    "endpoint": "/gb80/inform_webseite_dummy"
                },
                tool_call_id="get_eval_suites_1"
            )
        ],
        metadata={"phase": "retrieve_suites", "endpoint": "gb80/inform_webseite_dummy", "tools_used": ["get_evaluation_suites_api_getEvaluationSuites_post"]},
        description="Abruf der existierenden Evaluierungs-Suites"
    )
    convo.add_model_message("Ich rufe die Evaluierungs-Suites ab.")
    convo.add_tool_call(
        tool_call_id="get_eval_suites_1",
        tool_name="get_evaluation_suites_api_getEvaluationSuites_post",
        args={
            "endpoint": "/gb80/inform_webseite_dummy"
        }
    )
    convo.add_tool_response(
        tool_call_id="get_eval_suites_1",
        tool_name="get_evaluation_suites_api_getEvaluationSuites_post",
        content="*[Echte Evaluation Suites Daten vom API]*"
    )
    convo.add_model_message(case2_expected)

    # Case 3: Agent präsentiert existierende Suites und macht Vorschläge
    convo.add_user_message(
        "Was empfehlen Sie mir?"
    )
    case3_expected = """Ich habe die existierenden Testsuites für Ihren INFORM Webseiten-Copiloten gefunden:

*[Hier Liste der verfügbaren Testsuites mit Details]*

**Meine Empfehlung:** *[Konkrete Empfehlung basierend auf verfügbaren Suites]*

Möchten Sie eine dieser Suites ausführen, oder soll ich eine neue, individuell angepasste Testsuite für Sie erstellen?"""
    factory.create_conversation_case(
        name="INFORM Copilot Quality Testing – Suite-Empfehlung",
        conversation_turns=convo,
        expected_final_response=case3_expected,
        metadata={"phase": "recommendation", "endpoint": "gb80/inform_webseite_dummy"},
        description="Agent präsentiert existierende Suites und gibt Empfehlung"
    )
    convo.add_model_message(case3_expected)

    # Case 4: Nutzer entscheidet sich für Ausführung der Advanced Suite
    convo.add_user_message(
        "Führen Sie bitte die Advanced Quality Tests Suite aus."
    )
    case4_expected = "Ich starte die Evaluierungs-Suite für Ihren Copiloten. Die Ausführung kann einige Minuten dauern. Ich informiere Sie, sobald die Ergebnisse vorliegen."
    factory.create_conversation_case(
        name="INFORM Copilot Quality Testing – Suite Ausführung",
        conversation_turns=convo,
        expected_final_response=case4_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="execute_evaluation_suite_api_executeEvaluationSuite_post",
                args={
                    "endpoint": "/gb80/inform_webseite_dummy",
                    "suite_id": "inform_web_advanced_v2"
                },
                tool_call_id="execute_eval_suite_1"
            )
        ],
        metadata={"phase": "execution", "endpoint": "gb80/inform_webseite_dummy", "suite_id": "inform_web_advanced_v2", "tools_used": ["execute_evaluation_suite_api_executeEvaluationSuite_post"]},
        description="Ausführung der gewählten Evaluierungs-Suite"
    )
    convo.add_model_message("Ich führe die Evaluierungs-Suite aus.")
    convo.add_tool_call(
        tool_call_id="execute_eval_suite_1",
        tool_name="execute_evaluation_suite_api_executeEvaluationSuite_post",
        args={
            "endpoint": "/gb80/inform_webseite_dummy",
            "suite_id": "inform_web_advanced_v2"
        }
    )
    convo.add_tool_response(
        tool_call_id="execute_eval_suite_1",
        tool_name="execute_evaluation_suite_api_executeEvaluationSuite_post",
        content="*[Echte Execution Ergebnisse vom API]*"
    )
    convo.add_model_message(case4_expected)

    # Case 5: Agent präsentiert Testergebnisse
    convo.add_user_message(
        "Sind die Ergebnisse schon da? Zeigen Sie mir die Details."
    )
    case5_expected = """Die Evaluierung ist abgeschlossen! Hier sind die Ergebnisse:

*[Hier Zusammenfassung der Testergebnisse mit Statistiken]*

**Interpretation:**
*[Hier Interpretation der Ergebnisse und Bewertung der Copilot-Qualität]*

**Nächste Schritte:**
1. Detaillierte Fehleranalyse der fehlgeschlagenen Tests
2. Optimierung des Prompts oder der Knowledge-Quellen
3. Erneute Testausführung nach Verbesserungen

Möchten Sie die gespeicherten detaillierten Ergebnisse abrufen, um die Fehler zu analysieren?"""
    factory.create_conversation_case(
        name="INFORM Copilot Quality Testing – Ergebnispräsentation",
        conversation_turns=convo,
        expected_final_response=case5_expected,
        metadata={"phase": "results", "endpoint": "gb80/inform_webseite_dummy", "execution_id": "exec_20251112_001"},
        description="Agent präsentiert die Testergebnisse mit Interpretation"
    )
    convo.add_model_message(case5_expected)

    # Case 6: Nutzer möchte detaillierte Ergebnisse sehen
    convo.add_user_message(
        "Ja, zeigen Sie mir die detaillierten Ergebnisse, besonders die fehlgeschlagenen Tests."
    )
    case6_expected = """Hier sind die detaillierten Evaluierungsergebnisse:

*[Hier detaillierte Liste aller Tests mit Status, Erwartungen und tatsächlichen Ergebnissen]*

**Fehlgeschlagene Tests:**
*[Hier Liste fehlgeschlagener Tests mit spezifischen Fehleranalysen und Empfehlungen]*

**Erfolgreich:**
*[Hier Liste erfolgreicher Tests]*

**Handlungsempfehlungen:**
*[Hier priorisierte Handlungsempfehlungen basierend auf den Testergebnissen]*

Soll ich eine neue Testsuite mit Fokus auf die Problembereiche erstellen?"""
    factory.create_conversation_case(
        name="INFORM Copilot Quality Testing – Detaillierte Ergebnisse",
        conversation_turns=convo,
        expected_final_response=case6_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="get_stored_evaluation_results_api_getStoredEvaluationResults_post",
                args={
                    "endpoint": "/gb80/inform_webseite_dummy",
                    "execution_id": "exec_20251112_001"
                },
                tool_call_id="get_eval_results_1"
            )
        ],
        metadata={"phase": "detailed_results", "endpoint": "gb80/inform_webseite_dummy", "execution_id": "exec_20251112_001", "tools_used": ["get_stored_evaluation_results_api_getStoredEvaluationResults_post"]},
        description="Abruf und Präsentation der detaillierten Evaluierungsergebnisse"
    )
    convo.add_model_message("Ich rufe die detaillierten Ergebnisse ab.")
    convo.add_tool_call(
        tool_call_id="get_eval_results_1",
        tool_name="get_stored_evaluation_results_api_getStoredEvaluationResults_post",
        args={
            "endpoint": "/gb80/inform_webseite_dummy",
            "execution_id": "exec_20251112_001"
        }
    )
    convo.add_tool_response(
        tool_call_id="get_eval_results_1",
        tool_name="get_stored_evaluation_results_api_getStoredEvaluationResults_post",
        content="*[Echte detaillierte Evaluation Ergebnisse vom API]*"
    )
    convo.add_model_message(case6_expected)

    # Case 7: Nutzer möchte neue fokussierte Testsuite erstellen
    convo.add_user_message(
        "Ja, erstellen Sie bitte eine neue Testsuite, die sich auf die identifizierten Problembereiche konzentriert."
    )
    case7_expected = """Perfekt! Ich erstelle jetzt eine maßgeschneiderte Testsuite mit Fokus auf die Problembereiche:

*[Hier Details der neu erstellten fokussierten Testsuite]*

Die neue Testsuite wurde erfolgreich erstellt. Sie können diese Suite nach Ihren Optimierungen am Copiloten ausführen, um Verbesserungen zu messen.

**Empfohlener Workflow:**
1. Optimierungen basierend auf den Ergebnissen vornehmen
2. Neue fokussierte Suite ausführen
3. Vergleich der Ergebnisse mit der vorherigen Evaluierung
4. Iterative Verbesserung bis Zielquote erreicht

Möchten Sie jetzt mit den Optimierungen beginnen, oder haben Sie weitere Fragen zur Evaluierung?"""
    factory.create_conversation_case(
        name="INFORM Copilot Quality Testing – Neue fokussierte Suite erstellt",
        conversation_turns=convo,
        expected_final_response=case7_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="create_evaluation_suite_api_createEvaluationSuite_post",
                args={
                    "endpoint": "/gb80/inform_webseite_dummy",
                    "suite_name": "INFORM Web Quality Improvement Tests",
                    "suite_config": {
                        "focus_areas": ["pricing", "language", "technical_support", "context"],
                        "test_count": 15,
                        "categories": {
                            "pricing_accuracy": 5,
                            "language_consistency": 3,
                            "technical_support_quality": 4,
                            "context_preservation": 3
                        }
                    }
                },
                tool_call_id="create_eval_suite_1"
            )
        ],
        metadata={"phase": "create_suite", "endpoint": "gb80/inform_webseite_dummy", "tools_used": ["create_evaluation_suite_api_createEvaluationSuite_post"]},
        description="Erstellung einer neuen fokussierten Evaluierungs-Suite"
    )
    convo.add_model_message("Ich erstelle eine neue fokussierte Testsuite.")
    convo.add_tool_call(
        tool_call_id="create_eval_suite_1",
        tool_name="create_evaluation_suite_api_createEvaluationSuite_post",
        args={
            "endpoint": "/gb80/inform_webseite_dummy",
            "suite_name": "INFORM Web Quality Improvement Tests",
            "suite_config": {
                "focus_areas": ["pricing", "language", "technical_support", "context"],
                "test_count": 15,
                "categories": {
                    "pricing_accuracy": 5,
                    "language_consistency": 3,
                    "technical_support_quality": 4,
                    "context_preservation": 3
                }
            }
        }
    )
    convo.add_tool_response(
        tool_call_id="create_eval_suite_1",
        tool_name="create_evaluation_suite_api_createEvaluationSuite_post",
        content="*[Echte Suite Creation Bestätigung vom API]*"
    )
    convo.add_model_message(case7_expected)

    # Fehlerfall zum Abschluss (separate fehlerhafte Konversation)
    invalid_convo = factory.create_conversation_turns()
    invalid_convo.add_model_message("Ich starte die Evaluierungs-Unterhaltung falsch")
    try:
        factory.create_conversation_case(
            name="Ungültiger INFORM Copilot Eval Konversationstest",
            conversation_turns=invalid_convo,
            description="Dieser Test sollte bei der Validierung fehlschlagen"
        )
    except ValueError as e:
        print(f"Validierung hat erwarteten Fehler abgefangen: {e}")
    
    # Dataset erstellen
    dataset = factory.build_dataset("INFORM Copilot Quality Testing Suite")
    
    print(f"\nINFORM Copilot Quality Testing Dataset erstellt mit {len(dataset.cases)} Test-Fällen:")
    for case in dataset.cases:
        print(f"  - {case.name}")
    
    return dataset

def example_copilot_eval_validation():
    """Demonstriere Konversations-Validierungsfunktionen für Copilot Evaluation Use Cases."""
    
    factory = CaseFactory()
    
    # Beispiel 1: Gültige Copilot Evaluation Konversation
    valid_conversation = factory.create_conversation_turns()
    valid_conversation.add_user_message("Ich möchte die Qualität meines Copiloten testen")
    valid_conversation.add_model_message("Gerne! Ich helfe Ihnen mit Ally's Eval Tools.")
    valid_conversation.add_user_message("Welche Testsuites sind verfügbar?")
    
    errors = valid_conversation.validate()
    print(f"Gültige Copilot Eval Konversation Fehler: {errors}")  # Sollte leer sein
    
    # Beispiel 2: Ungültige Konversation - endet nicht mit Benutzer-Anfrage
    invalid_conversation = factory.create_conversation_turns()
    invalid_conversation.add_user_message("Hallo")
    invalid_conversation.add_model_message("Hi! Wie kann ich helfen?")
    # Fehlende finale Benutzer-Nachricht
    
    errors = invalid_conversation.validate()
    print(f"Ungültige Copilot Eval Konversation Fehler: {errors}")  # Sollte Validierungsfehler zeigen
    
    # Beispiel 3: Tool-Aufruf ohne Antwort
    incomplete_conversation = factory.create_conversation_turns()
    incomplete_conversation.add_user_message("Führen Sie die Testsuite aus")
    incomplete_conversation.add_tool_call("call_1", "execute_evaluation_suite_api_executeEvaluationSuite_post", {"endpoint": "/gb80/inform_webseite_dummy", "suite_id": "test_suite_1"})
    # Fehlende Tool-Antwort
    
    errors = incomplete_conversation.validate()
    print(f"Unvollständige Copilot Eval Konversation Fehler: {errors}")  # Sollte Tool-Aufruf-Fehler zeigen


if __name__ == "__main__":
    # Führe die Copilot Evaluation Beispiele aus
    dataset = example_inform_copilot_quality_testing()
    
    # Demonstriere Validierung
    print("\n--- Copilot Evaluation Validierungsbeispiele ---")
    example_copilot_eval_validation()
