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
from rasa_sdk.events import SlotSet, EventType, FollowupAction


class SolveProblemForm(FormAction):

    def name(self) -> Text:
        return "action_answer_problem"
    
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


class QnAPracticeForm(FormAction):
    def name(self) -> Text:
        print("came here")
        return "practice_form"
    
    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""
        return ["ready","answer"]
    
    def slot_mappings(self):
        print("mappings")
        return {
            "ready": [
                self.from_text(intent=None)
            ],
            "answer": [
                self.from_entity(entity="answer", intent="submit_answer")
            ]
        }

    def validate_ready(self,
                        value: Text,
                        dispatcher: CollectingDispatcher,
                        tracker: Tracker,
                        domain: Dict[Text, Any]):
        print("recieved ready or not - ", value)
        if tracker.latest_message.get('intent').get('name') == "confirmation.yes":
            file = open("actions/api_utils/questions.json")
            questionsJson = json.load(file)
            questions = questionsJson["problems"]
            qna = questions[random.randint(0,len(questions)-1)]
            question=qna.get("question")
            buttonDetails = {
                "Hint" : "/user.request_hint",
                "Submit": "/submit_answer{'question':'"+str(question)+"','answer':'"+str(qna.get("answer"))+"'}"
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
                text= "Solve "+str(question),
                buttons=buttons
            )
            return {"ready":"yes","question":question}
        else:
            return {"ready","no"}

    def validate_answer(self,
                            value: Text,
                            dispatcher: CollectingDispatcher,
                            tracker: Tracker,
                            domain: Dict[Text, Any]):
        print("recieved answer - ", value)
        if value.isnumeric():
            return {"answer": value}
        else:
            return {"answer": None}

    async def run(
        self,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        latest_intent = tracker.latest_message["intent"].get("name")
        if tracker.active_form.get("name", self.name()) != self.name():
            return self.deactivate() + [FollowupAction(name=self.name())]
        tracker.latest_action_name = "action_listen"
        return await super().run(dispatcher, tracker, domain)

    def submit(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
            question = str(tracker.slots.get("question"))
            user_answer = int(tracker.slots.get("answer"))
            actual_answer = eval(question)
            print(actual_answer)
            if user_answer == actual_answer:
                dispatcher.utter_message(response= "utter_you_did_it")
            else:
                dispatcher.utter_message(text="Oh NO! Wrong Answer.")
            dispatcher.utter_message(response= "utter_ask_another_problem")
            return [SlotSet("ready",None), SlotSet("answer",None), SlotSet("question",None)]