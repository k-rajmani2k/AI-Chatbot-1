import warnings
import random
import os
import sys
import pickle

from termcolor import colored

from .utils import sent_to_bow_array, get_intents
from .techniques.bow import train_bow_model
from .techniques.lstm import train_lstm_model
from .techniques.bert import train_bert_model
warnings.filterwarnings("ignore")


class CreateBot:

    words_filename = "words.pkl"
    tags_filename = "tags.pkl"
    model_filename = "model.h5"

    def __init__(self, filenames, technique="bow", mappings=None):
        self.filenames = filenames
        self.__create_filenames()
        self.mappings = mappings
        self.technique = technique

        self.__train_model()
        self.load_files()

    def __create_filenames(self):
        """
        If specified directory doesn't exist, it makes it and it contains 
        filename for words, tags and model
        """
        directory = self.filenames["dir"]
        if not os.path.exists(directory):
            os.mkdir(directory)

        self.filenames["words"] = os.path.join(
            directory, CreateBot.words_filename)

        self.filenames["tags"] = os.path.join(
            directory, CreateBot.tags_filename)

        self.filenames["model"] = os.path.join(
            directory, CreateBot.model_filename)

    def __train_model(self):
        if self.technique == "bow":
            self.model = train_bow_model(self.filenames)
        elif self.technique == "lstm":
            self.model = train_lstm_model(self.filenames)
        elif self.technique == "bert":
            self.model = train_bert_model(self.filenames)
        else:
            print(colored(
                "Please specify proper technique\nChoose among [bow | lstm | bert]", "red"))
            sys.exit(1)

    def load_files(self):
        # Loading words, tags and model
        self.words = pickle.load(open(self.filenames['words'], "rb"))
        self.tags = pickle.load(open(self.filenames['tags'], "rb"))
        self.intents = get_intents(self.filenames['intents'])


def get_response(intents_list, intents_json):
    # since sorted according to prob, 1st => highest
    tag = intents_list[0]["intent"]
    list_of_intents = intents_json["intents"]
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i["responses"])
            break
    return result


def predict_tag(bot_model, sentence: str, ERROR_THRESHOLD=0.25) -> list:
    bow = sent_to_bow_array(sentence, bot_model.words)
    res = bot_model.model.predict(bow)[0]
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)  # sort by prob

    return_list = []
    for r in results:
        return_list.append(
            {
                "intent": bot_model.tags[r[0]],
                "probability": str(r[1])
            })

    return return_list


def start_bot(bot_model, end_conversation=["/stop", "quit"],
              end_response="Thankyou for your time :)", speech=False):

    print(colored("\nBot is online, start conversation....\n", "red"))

    while True:
        message = input("> ")

        if message in end_conversation:
            print(end_response)
            break

        intents_list = predict_tag(bot_model, message)
        response = get_response(intents_list, bot_model.intents)
        print(colored(response, "blue"))


if __name__ == "__main__":

    filenames = {
        "intents": "./data/basic_intents.json",
        "dir": "dumps"
    }

    bot_model = CreateBot(filenames, technique="bow")
    start_bot(bot_model)
