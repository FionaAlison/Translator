from transformers import PegasusTokenizer, PegasusForConditionalGeneration
from torch.cuda import is_available, empty_cache
import gc

class TextSummariser: 
    _cache_dir: str = '/'.join(__file__.split('/')[:-2]+['models', 'pegasus_cache'])
    model_name: str = 'google/pegasus-xsum'
    device = 'cuda' if is_available() else 'cpu'
    tokenizer = PegasusTokenizer.from_pretrained(model_name, cache_dir=_cache_dir)
    model = PegasusForConditionalGeneration.from_pretrained(model_name, cache_dir=_cache_dir).to(device)

    def request(cls, src_text: str, padding: str = 'max_length', output_length: int = 500) -> str:
        tokens = cls.tokenizer.encode(src_text.strip(), truncation=True, padding=padding, return_tensors='pt').to(cls.device)
        summary = cls.model.generate(tokens ,max_length=output_length, length_penalty=2.6, num_beams=4)
        gc.collect()
        empty_cache()
        return cls.tokenizer.decode(summary[0], skip_special_tokens=True)

# with open('server/functionalities/text.txt', 'r') as file:
#     text: str = file.read()
#     sum_mod = TextSummariser()
#     answer = sum_mod.request(text, 'max_length', output_length=500)
#     print(answer, len(answer))