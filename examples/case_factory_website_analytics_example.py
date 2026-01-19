"""Example usage of CaseFactory for analytics use case - Corporate AI Team member analyzing existing copilot."""

from meta_ally.eval.case_factory import CaseFactory, create_tool_call_part


def example_inform_webseite_analytics():
    """
    Demonstrate test cases for Corporate AI Team member analyzing the INFORM website copilot.

    Returns:
        Dataset: A dataset containing test cases for the INFORM website copilot analytics.
    """
    factory = CaseFactory()

    # Verwende eine einzige ConversationTurns Instanz für alle Phasen
    convo = factory.create_conversation_turns()

    # Case 1: Initiale Anfrage - Nutzer möchte Analyse des bestehenden Copilots
    convo.add_user_message(
        "Hallo! Ich bin aus dem Corporate AI Team und maintaine den Copilot auf der INFORM Webseite. "
        "Ich würde gerne wissen, wie oft der Chatbot in letzter Zeit genutzt wurde, wie zufrieden die Nutzer "
        "sind und wie hoch die Kosten sind."
    )
    case1_expected = (
        "Hallo! Gerne unterstütze ich Sie bei der Analyse Ihres Copilots. "
        "Um die Nutzungsdaten, Bewertungen und Kosten abzurufen, benötige ich den Endpunktnamen. "
        "Wie lautet der Endpunkt Ihres Copilots?"
    )
    factory.create_conversation_case(
        name="INFORM Webseite Analytics - Initiale Anfrage",
        conversation_turns=convo,
        expected_final_response=case1_expected,
        description="Corporate AI Team Mitglied möchte Analytics für bestehenden Copilot"
    )

    # Füge erwartete Antwort als ModelResponse hinzu, um Gespräch fortzusetzen
    convo.add_model_message(case1_expected)

    # Case 2: Nutzer gibt Endpunktnamen an, Agent ruft alle drei Metriken ab
    convo.add_user_message(
        "Der Endpunkt ist /gb80/inform_webseite_dummy"
    )
    case2_expected = """Perfekt! Ich habe alle Daten abgerufen. Hier ist die vollständige Analyse für Ihren \
Copilot '/gb80/inform_webseite_dummy':

📊 **Nutzung (letzte 30 Tage):**
- <X> Sessions mit durchschnittlich <Y> Nachrichten pro Session
- Insgesamt <Z> Sessions seit Inbetriebnahme

⭐ **Nutzerzufriedenheit:**
- Durchschnittliche Bewertung: <A>/5 (<B> Bewertungen)
- Letzte 30 Tage: <C>/5 - die Zufriedenheit steigt!
- <D>% der Nutzer geben 4 oder 5 Sterne

💰 **Kosten (letzte 30 Tage):**
- Gesamtkosten: <E> €
- Durchschnittlich <F> € pro Tag
- Aktuelles Modell: <current_model>

Möchten Sie weitere Details zu bestimmten Bereichen oder Empfehlungen zur Kostenoptimierung?"""
    factory.create_conversation_case(
        name="INFORM Webseite Analytics - Vollständige Analyse präsentiert",
        conversation_turns=convo,
        expected_final_response=case2_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="ally_config_set_endpoint_name",
                args={"endpoint_name": "/gb80/inform_webseite_dummy"},
                tool_call_id="set_endpoint_name_1"
            ),
            create_tool_call_part(
                tool_name="ally_config_get_copilot_sessions",
                args={
                    "endpoint": "/gb80/inform_webseite_dummy",
                    "start_time": "<ISO_8601_start_time>",
                    "end_time": "<ISO_8601_end_time>"
                },
                tool_call_id="get_sessions_1"
            ),
            create_tool_call_part(
                tool_name="ally_config_get_copilot_ratings",
                args={
                    "endpoint": "/gb80/inform_webseite_dummy",
                    "start_time": "<ISO_8601_start_time>",
                    "end_time": "<ISO_8601_end_time>"
                },
                tool_call_id="get_ratings_1"
            ),
            create_tool_call_part(
                tool_name="ally_config_get_copilot_cost_daily",
                args={
                    "endpoint": "/gb80/inform_webseite_dummy",
                    "unit": "euro"
                },
                tool_call_id="get_costs_1"
            )
        ],
        description="Agent speichert Endpunkt und ruft Sessions, Ratings und Kosten ab"
    )

    convo.add_tool_call(
        tool_call_id="set_endpoint_name_1",
        tool_name="ally_config_set_endpoint_name",
        args={"endpoint_name": "/gb80/inform_webseite_dummy"}
    )
    convo.add_tool_response(
        tool_call_id="set_endpoint_name_1",
        tool_name="ally_config_set_endpoint_name",
        content="Endpoint name set to: /gb80/inform_webseite_dummy"
    )
    convo.add_tool_call(
        tool_call_id="get_sessions_1",
        tool_name="ally_config_get_copilot_sessions",
        args={
            "endpoint": "/gb80/inform_webseite_dummy",
            "start_time": "<ISO_8601_start_time>",
            "end_time": "<ISO_8601_end_time>"
        }
    )
    convo.add_tool_response(
        tool_call_id="get_sessions_1",
        tool_name="ally_config_get_copilot_sessions",
        content='<Session-Daten mit sessions Array: [{session_id, timestamp, messages: [{role, content, timestamp}]}]>'
    )
    convo.add_tool_call(
        tool_call_id="get_ratings_1",
        tool_name="ally_config_get_copilot_ratings",
        args={
            "endpoint": "/gb80/inform_webseite_dummy",
            "start_time": "<ISO_8601_start_time>",
            "end_time": "<ISO_8601_end_time>"
        }
    )
    convo.add_tool_response(
        tool_call_id="get_ratings_1",
        tool_name="ally_config_get_copilot_ratings",
        content='<Rating-Daten als Array: [{endpoint, rating, user_name, model_name, session_id, timestamp}]>'
    )
    convo.add_tool_call(
        tool_call_id="get_costs_1",
        tool_name="ally_config_get_copilot_cost_daily",
        args={
            "endpoint": "/gb80/inform_webseite_dummy",
            "unit": "euro"
        }
    )
    convo.add_tool_response(
        tool_call_id="get_costs_1",
        tool_name="ally_config_get_copilot_cost_daily",
        content='<Kosten-Daten mit daily_data Array: [{date, cost/tokens, model_name}] für letzte 30 Tage>'
    )
    convo.add_model_message(case2_expected)

    # Case 3: Nutzer bittet um Kostenoptimierung
    convo.add_user_message(
        "Danke für die Analyse! Gibt es Möglichkeiten, die Kosten zu optimieren?"
    )
    case3_expected = """Ja, auf jeden Fall! Lassen Sie mich die verfügbaren Modelle prüfen, um \
günstigere Alternativen zu identifizieren.

📊 **Optimierungsansätze:**

Basierend auf den verfügbaren Modellen und Ihrer aktuellen Nutzung könnte ein Wechsel zu einem \
kostengünstigeren Modell erhebliche Einsparungen bringen, ohne die Qualität wesentlich zu \
beeinträchtigen.

Möchten Sie Details zu den verfügbaren günstigeren Modelloptionen?"""

    factory.create_conversation_case(
        name="INFORM Webseite Analytics - Kostenoptimierung anfragen",
        conversation_turns=convo,
        expected_final_response=case3_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="ai_knowledge_list_models",
                args={},
                tool_call_id="list_models_1"
            )
        ],
        description="Agent prüft verfügbare Modelle für Kostenoptimierung"
    )

    convo.add_tool_call(
        tool_call_id="list_models_1",
        tool_name="ai_knowledge_list_models",
        args={}
    )
    convo.add_tool_response(
        tool_call_id="list_models_1",
        tool_name="ai_knowledge_list_models",
        content='<Liste verfügbarer Modelle: [{label, name, description, enabled}]>'
    )
    convo.add_model_message(case3_expected)

    # Case 4: Nutzer fragt nach Details zu günstigeren Modellen
    convo.add_user_message(
        "Ja, welche günstigeren Modelle stehen zur Verfügung?"
    )
    case4_expected = """Basierend auf den verfügbaren Modellen empfehle ich folgende Alternativen:

📋 **Verfügbare günstigere Modelle:**

1. **<günstigeres_modell_1>**
   - <Beschreibung_Modell_1>
   - Geschätzte Ersparnis: <X>%

2. **<günstigeres_modell_2>**
   - <Beschreibung_Modell_2>
   - Geschätzte Ersparnis: <Y>%

💰 **Kostenvergleich (basierend auf aktueller Nutzung):**
- Aktuell mit <current_model>: <current_costs> € (letzte 30 Tage)
- Mit <günstigeres_modell_1>: ca. <estimated_new_costs> €
- **Potenzielle Ersparnis: ~<monthly_savings> €/Monat**

⚠️ **Empfehlung:**
Ich würde einen A/B-Test über <test_duration> empfehlen, um die Qualität bei reduzier ten Kosten zu validieren.

Möchten Sie, dass ich einen Test-Endpoint mit einem der günstigeren Modelle einrichte?"""

    factory.create_conversation_case(
        name="INFORM Webseite Analytics - Details zu Kostenoptimierung",
        conversation_turns=convo,
        expected_final_response=case4_expected,
        description="Agent gibt detaillierte Kostenanalyse und konkrete Empfehlungen für Modellwechsel"
    )
    convo.add_model_message(case4_expected)

    # Case 5: Nutzer möchte weitere Informationen zu Sessions
    convo.add_user_message(
        "Danke für die Info! Können Sie mir noch mehr Details zu den Sessions zeigen? "
        "Wann wird der Copilot am meisten genutzt?"
    )
    case5_expected = """Basierend auf den Session-Daten der letzten 30 Tage:

📈 **Nutzungsmuster:**
- <sessions_count> Sessions insgesamt
- Durchschnittlich <avg_messages> Nachrichten pro Session
- Aktivste Sessions: <top_sessions_description>

Um detailliertere Zeitanalysen durchzuführen (z.B. Nutzung nach Uhrzeit, Wochentag), bräuchte ich Zugriff \
auf erweiterte Analytics-Tools oder Sie können die vollständigen Session-Daten exportieren.

Soll ich noch weitere Metriken für Sie abrufen oder haben Sie andere Fragen zur Copilot-Performance?"""

    factory.create_conversation_case(
        name="INFORM Webseite Analytics - Zusätzliche Session-Details",
        conversation_turns=convo,
        expected_final_response=case5_expected,
        description="Agent bietet zusätzliche Insights zu Nutzungsmustern"
    )
    convo.add_model_message(case5_expected)

    # Dataset erstellen
    dataset = factory.build_dataset("INFORM Webseite Copilot Analytics Suite")

    print(f"INFORM Webseite Analytics Test-Dataset erstellt mit {len(dataset.cases)} Test-Fällen:")
    for case in dataset.cases:
        print(f"  - {case.name}")

    return dataset


if __name__ == "__main__":
    # Führe die Analytics Beispiele aus
    dataset = example_inform_webseite_analytics()

    case_1 = dataset.cases[0]
    from meta_ally.eval.case_factory import MessageHistoryCase
    from meta_ally.ui.visualization import visualize_single_case

    print("\n--- Beispiel Fall 1 (Initiale Anfrage) ---")
    print(f"Name: {case_1.name}")
    message_history_case = MessageHistoryCase.from_case(case_1)

    # Visualize the first case
    print("\n=== Visualizing Case 1 ===")
    visualize_single_case(message_history_case)

    case_2 = dataset.cases[1]
    print("\n--- Beispiel Fall 2 (Daten werden abgerufen) ---")
    print(f"Name: {case_2.name}")
    message_history_case_2 = MessageHistoryCase.from_case(case_2)

    print("\n=== Visualizing Case 2 (with tool calls for analytics) ===")
    visualize_single_case(message_history_case_2)

    case_3 = dataset.cases[2]
    print("\n--- Beispiel Fall 3 (Ergebnisse präsentiert) ---")
    print(f"Name: {case_3.name}")
    message_history_case_3 = MessageHistoryCase.from_case(case_3)

    print("\n=== Visualizing Case 3 (Results presentation) ===")
    visualize_single_case(message_history_case_3)

    last_case = dataset.cases[-1]

    print("\n -- Komplette Konversation -- ")
    print(f"Name: {last_case.name}")
    message_history_case_last = MessageHistoryCase.from_case(last_case)
    print("\n=== Visualizing Last Case ===")
    visualize_single_case(message_history_case_last)
