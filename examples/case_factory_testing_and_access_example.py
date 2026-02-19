"""Example usage of CaseFactory for testing and access management use case."""

from meta_ally.eval.case_factory import CaseFactory, create_tool_call_part


def example_testing_and_access_management():
    """
    Demonstrate test cases for Corporate AI Team member testing copilot and managing access.

    Returns:
        Dataset: A dataset containing test cases for copilot testing and access management.
    """
    factory = CaseFactory()

    # Use a single ConversationTurns instance for all phases
    convo = factory.create_conversation_turns()

    # Case 1: Initial request - User wants to test the copilot
    convo.add_user_message(
        "Hallo! Ich bin in GB80 und meine Projektnummer ist 80000. Ich maintaine den Copilot auf unserer "
        "Webseite und möchte testen, ob er wie gewünscht funktioniert. Der Endpunkt ist "
        "/gb80/inform_webseite_dummy."
    )
    case1_expected = (
        "Hallo! Das ist eine gute Idee, den Copilot regelmäßig zu testen. "
        "Sie haben zwei Möglichkeiten:\n\n"
        "1. **Webportal**: Sie können den Copilot direkt im Webportal in der Chat-UI testen.\n"
        "2. **Evaluation Suite**: Ich kann Ihnen helfen, eine Evaluation Suite zu erstellen, "
        "mit der Sie systematisch mehrere Testfälle definieren und automatisiert ausführen können.\n\n"
        "Welche Option bevorzugen Sie?"
    )
    factory.create_conversation_case(
        name="Testing & Access - Initial Request",
        conversation_turns=convo,
        expected_final_response=case1_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="set_endpoint_name",
                args={"endpoint_name": "/gb80/inform_webseite_dummy"},
                tool_call_id="set_endpoint_1"
            )
        ],
        description="User wants to test their copilot, agent offers testing options"
    )

    convo.add_tool_call(
        tool_call_id="set_endpoint_1",
        tool_name="set_endpoint_name",
        args={"endpoint_name": "/gb80/inform_webseite_dummy"}
    )
    convo.add_tool_response(
        tool_call_id="set_endpoint_1",
        tool_name="set_endpoint_name",
        content="Endpoint name set to: /gb80/inform_webseite_dummy"
    )
    convo.add_model_message(case1_expected)

    # Case 2: User chooses evaluation suite
    convo.add_user_message(
        "Können Sie mir helfen, eine Evaluation Suite einzurichten?"
    )
    case2_expected = (
        "Natürlich! Um eine Evaluation Suite zu erstellen, benötige ich folgende Informationen:\n\n"
        "1. **Name der Test-Suite**: Ein aussagekräftiger Name für Ihre Evaluation Suite\n"
        "2. **Testfälle**: Eine Liste von Testfällen, wobei jeder Testfall besteht aus:\n"
        "   - Einer Eingabe (Input): Die Frage oder Anfrage, die getestet werden soll\n"
        "   - Einer erwarteten Ausgabe (Expected Output): Was der Copilot idealerweise antworten sollte\n\n"
        "Welchen Namen möchten Sie für die Suite verwenden und welche Testfälle sollen enthalten sein?"
    )
    factory.create_conversation_case(
        name="Testing & Access - Choose Evaluation Suite",
        conversation_turns=convo,
        expected_final_response=case2_expected,
        description="User chooses evaluation suite, agent explains what's needed"
    )

    convo.add_model_message(case2_expected)

    # Case 3: User provides suite name and test cases
    convo.add_user_message(
        "Der Name soll 'website_test_suite' sein. Hier sind einige Testfälle:\n\n"
        "1. Input: 'Was macht INFORM?', Expected: 'INFORM ist ein führender Anbieter von Software für...'\n"
        "2. Input: 'Welche Produkte bietet INFORM an?',"
        "Expected: 'INFORM bietet verschiedene Produkte an, darunter...'\n"
        "3. Input: 'Wie kann ich INFORM kontaktieren?', Expected: 'Sie können INFORM über folgende Kanäle erreichen...'"
    )
    case3_expected = (
        "Perfekt! Ich habe die Evaluation Suite 'website_test_suite' erfolgreich erstellt und "
        "alle drei Testfälle hinzugefügt:\n\n"
        "✅ Testfall 1: 'Was macht INFORM?'\n"
        "✅ Testfall 2: 'Welche Produkte bietet INFORM an?'\n"
        "✅ Testfall 3: 'Wie kann ich INFORM kontaktieren?'\n\n"
        "Die Suite ist jetzt bereit. Soll ich sie jetzt ausführen?"
    )
    factory.create_conversation_case(
        name="Testing & Access - Create Suite and Add Cases",
        conversation_turns=convo,
        expected_final_response=case3_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="ally_config_create_copilot_evaluation_suite",
                args={
                    "test_suite_name": "website_test_suite",
                    "endpoint": "/gb80/inform_webseite_dummy"
                },
                tool_call_id="create_suite_1"
            ),
            create_tool_call_part(
                tool_name="ally_config_add_copilot_evaluation_test_cases",
                args={
                    "test_suite_name": "website_test_suite",
                    "endpoint": "/gb80/inform_webseite_dummy",
                    "test_cases": [
                        {
                            "name": "test_inform_company",
                            "user_input": "Was macht INFORM?",
                            "expected_response": "INFORM ist ein führender Anbieter von Software für..."
                        },
                        {
                            "name": "test_inform_products",
                            "user_input": "Welche Produkte bietet INFORM an?",
                            "expected_response": "INFORM bietet verschiedene Produkte an, darunter..."
                        },
                        {
                            "name": "test_inform_contact",
                            "user_input": "Wie kann ich INFORM kontaktieren?",
                            "expected_response": "Sie können INFORM über folgende Kanäle erreichen..."
                        }
                    ]
                },
                tool_call_id="update_suite_1"
            )
        ],
        description="Agent creates evaluation suite and adds test cases"
    )

    convo.add_tool_call(
        tool_call_id="create_suite_1",
        tool_name="ally_config_create_copilot_evaluation_suite",
        args={
            "test_suite_name": "website_test_suite",
            "endpoint": "/gb80/inform_webseite_dummy"
        }
    )
    convo.add_tool_response(
        tool_call_id="create_suite_1",
        tool_name="ally_config_create_copilot_evaluation_suite",
        content="Evaluation suite 'website_test_suite' created successfully for endpoint /gb80/inform_webseite_dummy"
    )
    convo.add_tool_call(
        tool_call_id="update_suite_1",
        tool_name="ally_config_add_copilot_evaluation_test_cases",
        args={
            "test_suite_name": "website_test_suite",
            "endpoint": "/gb80/inform_webseite_dummy",
            "test_cases": [
                {
                    "name": "test_inform_company",
                    "user_input": "Was macht INFORM?",
                    "expected_response": "INFORM ist ein führender Anbieter von Software für..."
                },
                {
                    "name": "test_inform_products",
                    "user_input": "Welche Produkte bietet INFORM an?",
                    "expected_response": "INFORM bietet verschiedene Produkte an, darunter..."
                },
                {
                    "name": "test_inform_contact",
                    "user_input": "Wie kann ich INFORM kontaktieren?",
                    "expected_response": "Sie können INFORM über folgende Kanäle erreichen..."
                }
            ]
        }
    )
    convo.add_tool_response(
        tool_call_id="update_suite_1",
        tool_name="ally_config_add_copilot_evaluation_test_cases",
        content="Added 3 test cases to evaluation suite 'website_test_suite'"
    )
    convo.add_model_message(case3_expected)

    # Case 4: User wants to run the suite
    convo.add_user_message("Ja, bitte führen Sie die Suite aus.")
    case4_expected = (
        "Ich habe versucht, die Evaluation Suite auszuführen, aber es ist ein interner Fehler aufgetreten. "
        "Die Suite konnte nicht erfolgreich ausgeführt werden.\n\n"
        "⚠️ **Fehler**: Internal server error during test execution\n\n"
        "Soll ich es erneut versuchen oder möchten Sie den Fehler zunächst untersuchen?"
    )
    factory.create_conversation_case(
        name="Testing & Access - Execute Suite (Error)",
        conversation_turns=convo,
        expected_final_response=case4_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="ally_config_execute_copilot_evaluation_suite",
                args={
                    "test_suite_name": "website_test_suite",
                    "endpoint": "/gb80/inform_webseite_dummy"
                },
                tool_call_id="execute_suite_1"
            )
        ],
        description="Agent attempts to execute suite but encounters error"
    )

    convo.add_tool_call(
        tool_call_id="execute_suite_1",
        tool_name="ally_config_execute_copilot_evaluation_suite",
        args={
            "test_suite_name": "website_test_suite",
            "endpoint": "/gb80/inform_webseite_dummy"
        }
    )
    convo.add_tool_response(
        tool_call_id="execute_suite_1",
        tool_name="ally_config_execute_copilot_evaluation_suite",
        content="Error: Internal server error during test execution"
    )
    convo.add_model_message(case4_expected)

    # Case 5: User mentions known issue and switches to access management
    convo.add_user_message(
        "Nein, ich habe von meinen Kollegen gehört, dass es im Moment kaputt ist. "
        "Aber ich möchte jetzt meinem neuen Kollegen mit der E-Mail-Adresse colleague@inform-software.com "
        "Zugriff geben, damit er den Copilot nutzen kann. Er soll den Copilot nur ansehen und verwenden können, "
        "aber nichts konfigurieren."
    )
    case5_expected = (
        "Verstanden! Ich habe für Ihren Kollegen eine neue Rolle erstellt und ihm Zugriff gegeben:\n\n"
        "✅ **Rolle erstellt**: 'Copilot Viewer & User'\n"
        "✅ **Berechtigungen zugewiesen**:\n"
        "   - Copilot ansehen (view_copilot)\n"
        "   - Copilot verwenden (use_copilot)\n"
        "✅ **Benutzer hinzugefügt**: colleague@inform-software.com\n\n"
        "Ihr Kollege kann jetzt den Copilot auf /gb80/inform_webseite_dummy nutzen, "
        "hat aber keine Konfigurations- oder Administrationsrechte.\n\n"
        "Gibt es noch etwas, bei dem ich Ihnen helfen kann?"
    )
    factory.create_conversation_case(
        name="Testing & Access - Add Colleague Access",
        conversation_turns=convo,
        expected_final_response=case5_expected,
        expected_final_tool_calls=[
            create_tool_call_part(
                tool_name="ally_config_add_role",
                args={
                    "resource_type": "endpoint",
                    "resource_name": "/gb80/inform_webseite_dummy",
                    "role": "Copilot Viewer & User"
                },
                tool_call_id="create_role_1"
            ),
            create_tool_call_part(
                tool_name="ally_config_grant_permission",
                args={
                    "resource_type": "endpoint",
                    "resource_name": "/gb80/inform_webseite_dummy",
                    "role": "Copilot Viewer & User",
                    "permission": "endpoint.view"
                },
                tool_call_id="add_permission_1"
            ),
            create_tool_call_part(
                tool_name="ally_config_grant_permission",
                args={
                    "resource_type": "endpoint",
                    "resource_name": "/gb80/inform_webseite_dummy",
                    "role": "Copilot Viewer & User",
                    "permission": "endpoint.use"
                },
                tool_call_id="add_permission_2"
            ),
            create_tool_call_part(
                tool_name="ally_config_add_user",
                args={
                    "resource_type": "endpoint",
                    "resource_name": "/gb80/inform_webseite_dummy",
                    "role": "Copilot Viewer & User",
                    "user": "colleague@inform-software.com"
                },
                tool_call_id="add_user_1"
            )
        ],
        description="Agent creates role with view/use permissions and adds colleague"
    )

    convo.add_tool_call(
        tool_call_id="create_role_1",
        tool_name="ally_config_add_role",
        args={
            "resource_type": "endpoint",
            "resource_name": "/gb80/inform_webseite_dummy",
            "role": "Copilot Viewer & User"
        }
    )
    convo.add_tool_response(
        tool_call_id="create_role_1",
        tool_name="ally_config_add_role",
        content="Role 'Copilot Viewer & User' created successfully"
    )
    convo.add_tool_call(
        tool_call_id="add_permission_1",
        tool_name="ally_config_grant_permission",
        args={
            "resource_type": "endpoint",
            "resource_name": "/gb80/inform_webseite_dummy",
            "role": "Copilot Viewer & User",
            "permission": "endpoint.view"
        }
    )
    convo.add_tool_response(
        tool_call_id="add_permission_1",
        tool_name="ally_config_grant_permission",
        content="Permission 'endpoint.view' added to role 'Copilot Viewer & User'"
    )
    convo.add_tool_call(
        tool_call_id="add_permission_2",
        tool_name="ally_config_grant_permission",
        args={
            "resource_type": "endpoint",
            "resource_name": "/gb80/inform_webseite_dummy",
            "role": "Copilot Viewer & User",
            "permission": "endpoint.use"
        }
    )
    convo.add_tool_response(
        tool_call_id="add_permission_2",
        tool_name="ally_config_grant_permission",
        content="Permission 'endpoint.use' added to role 'Copilot Viewer & User'"
    )
    convo.add_tool_call(
        tool_call_id="add_user_1",
        tool_name="ally_config_add_user",
        args={
            "resource_type": "endpoint",
            "resource_name": "/gb80/inform_webseite_dummy",
            "role": "Copilot Viewer & User",
            "user": "colleague@inform-software.com"
        }
    )
    convo.add_tool_response(
        tool_call_id="add_user_1",
        tool_name="ally_config_add_user",
        content="User 'colleague@inform-software.com' added to role 'Copilot Viewer & User' "
        "for endpoint /gb80/inform_webseite_dummy"
    )
    convo.add_model_message(case5_expected)

    # Build dataset
    dataset = factory.build_dataset("INFORM Website Testing & Access Management Suite")

    print(f"Testing & Access Management Test-Dataset created with {len(dataset.cases)} test cases:")
    for case in dataset.cases:
        print(f"  - {case.name}")

    return dataset


if __name__ == "__main__":
    # Execute the testing and access management examples
    dataset = example_testing_and_access_management()

    case_1 = dataset.cases[0]
    from meta_ally.eval.case_factory import MessageHistoryCase
    from meta_ally.ui.visualization import visualize_single_case

    print("\n--- Example Case 1 (Initial Request) ---")
    print(f"Name: {case_1.name}")
    message_history_case = MessageHistoryCase.from_case(case_1)

    # Visualize the first case
    print("\n=== Visualizing Case 1 ===")
    visualize_single_case(message_history_case)

    case_2 = dataset.cases[1]
    print("\n--- Example Case 2 (Choose Evaluation Suite) ---")
    print(f"Name: {case_2.name}")
    message_history_case_2 = MessageHistoryCase.from_case(case_2)

    print("\n=== Visualizing Case 2 ===")
    visualize_single_case(message_history_case_2)

    case_3 = dataset.cases[2]
    print("\n--- Example Case 3 (Create Suite and Add Cases) ---")
    print(f"Name: {case_3.name}")
    message_history_case_3 = MessageHistoryCase.from_case(case_3)

    print("\n=== Visualizing Case 3 ===")
    visualize_single_case(message_history_case_3)

    case_4 = dataset.cases[3]
    print("\n--- Example Case 4 (Execute Suite with Error) ---")
    print(f"Name: {case_4.name}")
    message_history_case_4 = MessageHistoryCase.from_case(case_4)

    print("\n=== Visualizing Case 4 ===")
    visualize_single_case(message_history_case_4)

    last_case = dataset.cases[-1]
    print("\n --- Complete Conversation --- ")
    print(f"Name: {last_case.name}")
    message_history_case_last = MessageHistoryCase.from_case(last_case)
    print("\n=== Visualizing Last Case (Complete Conversation) ===")
    visualize_single_case(message_history_case_last)
