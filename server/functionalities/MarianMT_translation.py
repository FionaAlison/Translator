from transformers import MarianTokenizer, MarianMTModel
from abc import ABC, abstractclassmethod
import os
import warnings

class TextTranslator(ABC):

    cache_dir: str = '/'.join(__file__.split('/')[:-2]+ ['models'])

    @abstractclassmethod
    def request(cls, source_lang: str, target_lang, text: str) -> str:
        warnings.filterwarnings("ignore")
        try: 
            model_name = f'Helsinki-NLP/opus-mt-{source_lang}-{target_lang}'
            model = MarianMTModel.from_pretrained(os.path.join(cls.cache_dir, model_name), cache_dir=cls.cache_dir)
            tokenizer = MarianTokenizer.from_pretrained(os.path.join(cls.cache_dir, model_name), cache_dir=cls.cache_dir)
        except EnvironmentError:
            try:
                model_name = f'Helsinki-NLP/opus-mt-{source_lang}-{target_lang}'
                model = MarianMTModel.from_pretrained(model_name, cache_dir=cls.cache_dir)
                tokenizer = MarianTokenizer.from_pretrained(model_name, cache_dir=cls.cache_dir)
            except Exception:
                return 'Language translatoin not supported'
      

        input_ids = tokenizer.encode(text, return_tensors='pt')
        translation_ids = model.generate(input_ids)
        translated_text = tokenizer.decode(translation_ids[0], skip_special_tokens=True)
        warnings.resetwarnings()

        return translated_text
    

with open('server/functionalities/text.txt', 'r') as file:
    print(TextTranslator.request('en', 'no', file.read()))

