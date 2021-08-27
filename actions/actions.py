import json
from math import exp
from os import set_inheritable
import random
import re
from .api_utils.base import InavlidExpressionException

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction


class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        file = open("actions/api_utils/questions.json")
        questionsJson = json.load(file)
        questions = questionsJson["problems"]
        msgText = questions[random.randint(0,len(questions)-1)]
        buttonDetails = {
            "Hint" : "/hint",
            "Submit": "/answer{'question':'"+msgText["problem"]+"','answer':'"+msgText["answer"]+"'}"
        }
        buttons = []
        for button in buttonDetails:
            buttons.append(
                {
                    "title": "{}".format(button),
                    "payload": buttonDetails[button],
                }
            )

        dispatcher.utter_message(
            text= "what is the answer of "+msgText["problem"]+"?",
            image=None,
            json_message=None,
            response=None,
            attachment=None,
            buttons=buttons,
            elements=None,
        )

        return []

class SolveProblemForm(FormAction):

    def name(self) -> Text:
        return "action_solve_problem"
    
    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""
        return ["expression"]
    
    def slot_mappings(self):
        return {
            "expression": [
                self.from_entity(entity="expression", intent="solve"),
                self.from_entity(entity="expression", intent="wanthelp"),
                self.from_entity(entity="expression", intent=None),
                self.from_text(intent="solve")
            ]
        }
    def validate_expression(self,
                            value: Text,
                            dispatcher: CollectingDispatcher,
                            tracker: Tracker,
                            domain: Dict[Text, Any]):
        print("recieved expression - ", value)
        if type(value) is not list:
            value = [value]
        print(value)
        for expression in value:
            try:
                eval(expression)
                if expression.isnumeric():
                    raise InavlidExpressionException
                else:
                    return {'expression': expression}
            except InavlidExpressionException:
                expression = self.solve_again(tracker.latest_message.get('text'))
            except SyntaxError:
                expression = self.solve_again(tracker.latest_message.get('text'))
            except ZeroDivisionError:
                expression = None
                dispatcher.utter_message(response= "utter_invalid_division")
            except Exception:
                expression = None
                dispatcher.utter_message(
                        text= None,
                        image=None,
                        json_message=None,
                        response="utter_invalid_expression",
                        attachment=None,
                        buttons=None,
                        elements=None,
                    )
        return {'expression': expression}

    def solve_again(self,msg):
        print(msg)
        reg = re.findall(r'[0-9.]+|[*/+\-\^\(\)]', msg)
        print(reg)
        expression = ''.join(reg)
        return expression
    def submit(self,
               dispatcher: CollectingDispatcher,
               tracker: Tracker,
               domain: Dict[Text, Any]) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""
        question = tracker.get_slot("expression")
        try:
            answer = eval(question)
        except:
            answer = None
        print("answer is : ", answer)
        if answer is not None:
            dispatcher.utter_message(
                text= "Here you go, Answer is : "+ str(round(answer, 2)),
                image=None,
                json_message=None,
                response=None,
                attachment=None,
                buttons=None,
                elements=None,
            )
        else:
            dispatcher.utter_message(
                text= None,
                image=None,
                json_message=None,
                response="utter_invalid_expression",
                attachment=None,
                buttons=None,
                elements=None,
            )
        return []