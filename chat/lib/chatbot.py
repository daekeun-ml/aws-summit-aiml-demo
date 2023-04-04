import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

PROMPT_DICT = {
    "prompt_input": (
        "Below is an instruction that describes a task, paired with an input that provides further context.\n"
        "아래는 작업을 설명하는 명령어와 추가적 맥락을 제공하는 입력이 짝을 이루는 예제입니다.\n\n"
        "Write a response that appropriately completes the request.\n요청을 적절히 완료하는 응답을 작성하세요.\n\n"
        "### Instruction(명령어):\n{instruction}\n\n### Input(입력):\n{context}\n\n### Response(응답):"
    ),
    "prompt_no_input": (
        "Below is an instruction that describes a task.\n"
        "아래는 작업을 설명하는 명령어입니다.\n\n"
        "Write a response that appropriately completes the request.\n명령어에 따른 요청을 적절히 완료하는 응답을 작성하세요.\n\n"
        "### Instruction(명령어):\n{instruction}\n\n### Response(응답):"
    ),
}


def setup_model(model_name: str, cache_dir: str):
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        cache_dir=cache_dir
    )
    if device == "cuda":
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map='auto',
            cache_dir=cache_dir,
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name, device_map={"": device},
            low_cpu_mem_usage=True,
            cache_dir=cache_dir,
        )
    model.eval()
    return tokenizer, model


def generate(
    tokenizer: AutoTokenizer,
    model: AutoModelForCausalLM,
    prompt: str,
    context: str = None,
    top_p: float = 0.8,
    top_k: int = 40,
    max_new_tokens: int = 128,
    temperature: float = 0.1,
):
    if context:
        x = PROMPT_DICT['prompt_input'].format(instruction=prompt, context=context)
    else:
        x = PROMPT_DICT['prompt_no_input'].format(instruction=prompt)

    input_ids = tokenizer.encode(x, return_tensors="pt").to(model.device)
    with torch.no_grad():
        gen_tokens = model.generate(
            input_ids=input_ids,
            max_new_tokens=max_new_tokens, 
            num_return_sequences=1,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            no_repeat_ngram_size=6,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(gen_tokens[0], skip_special_tokens=True)[len(x):]


if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()

    model_name = os.environ['MODEL_NAME']
    cache_dir = os.environ['CACHE_DIR']
    tokenizer, model = setup_model(model_name, cache_dir)

    prompt = "입력받은 숫자가 prime number 인지 검사하는 python 코드"
    generation = generate(tokenizer, model, prompt)
    print(generation)