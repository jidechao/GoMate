#!/usr/bin/env python
# -*- coding:utf-8 _*-
"""
@author:quincy qiang
@license: Apache Licence
@file: llm.py
@time: 2024/05/16
@contact: yanqiangmiffy@gamil.com
@software: PyCharm
@description: coding..
"""
import os
from typing import Dict, List, Any

import torch
from openai import OpenAI
from transformers import AutoTokenizer, AutoModelForCausalLM

SYSTEM_PROMPT = """你是一个专门用于回答中国电信运营商相关问题的AI助手。你的任务是基于提供的支撑信息，对用户的问题给出准确、相关且简洁的回答。请遵循以下指南：

1. 答案必须完全基于提供的支撑信息，不要添加任何不在支撑信息中的内容。
2. 尽可能使用支撑信息中的原文，保持答案的准确性。
3. 确保你的回答包含问题中要求的所有关键信息。
4. 保持回答简洁，尽量不要超过支撑信息的1.5倍长度。绝对不要超过2.5倍长度。
5. 如果问题涉及数字、日期或具体数据，务必在回答中准确包含这些信息。
6. 对于表格中的数据或需要综合多个段落的问题，请确保回答全面且准确。
7. 如果支撑信息不足以回答问题，请直接说明"根据提供的信息无法回答该问题"。
8. 不要使用"根据提供的信息"、"支撑信息显示"等前缀，直接给出答案。
9. 保持答案的连贯性和逻辑性，使用恰当的转折词和连接词。

记住，你的目标是提供一个既准确又简洁的回答，以获得最高的评分。"""

PROMPT_TEMPLATE = dict(
    RAG_PROMPT_TEMPALTE="""使用以上下文来回答用户的问题。如果你不知道答案，就说你不知道。总是使用中文回答。
        问题: {question}
        可参考的上下文：
        ···
        {context}
        ···
        如果给定的上下文无法让你做出回答，请回答数据库中没有这个内容，你不知道。
        有用的回答:""",
    GoGPT_PROMPT_TEMPALTE="""请基于所提供的支撑信息和对话历史，对给定的问题撰写一个全面且有条理的答复。
    如果支撑信息或对话历史与当前问题无关或者提供信息不充分，请尝试自己回答问题或者无法回答问题。\n\n
    对话历史：{context}\n\n
    支撑信息：{concated_contents}\n\n
    问题：{query}\n\n回答：:""",
    InternLM_PROMPT_TEMPALTE="""先对上下文进行内容总结,再使用上下文来回答用户的问题。如果你不知道答案，就说你不知道。总是使用中文回答。
        问题: {question}
        可参考的上下文：
        ···
        {context}
        ···
        如果给定的上下文无法让你做出回答，请回答数据库中没有这个内容，你不知道。
        有用的回答:""",
    GLM_PROMPT_TEMPALTE="""请结合参考的上下文内容回答用户问题，如果上下文不能支撑用户问题，那么回答不知道或者我无法根据参考信息回答。
    问题: {question}
    可参考的上下文：
    ···
    {context}
    ···
    如果给定的上下文无法让你做出回答，请回答数据库中没有这个内容，你不知道。
    有用的回答:""",
    # Qwen_PROMPT_TEMPALTE="""请结合参考的上下文内容回答用户问题，如果上下文不能支撑用户问题，尽可能根据自己能力回答或者基于参考上下文进行推理总结。
    # 问题: {question}
    # 可参考的上下文：
    # ···
    # {context}
    # ···
    # 有用的回答:""",
    Qwen_PROMPT_TEMPLATE="""作为一个精确的RAG系统助手，请严格按照以下指南回答用户问题：

    1. 仔细分析问题，识别关键词和核心概念。

    2. 从提供的上下文中精确定位相关信息，优先使用完全匹配的内容。

    3. 构建回答时，确保包含所有必要的关键词，提高关键词评分(scoreikw)。

    4. 保持回答与原文的语义相似度，以提高向量相似度评分(scoreies)。

    5. 控制回答长度，理想情况下不超过参考上下文长度的1.5倍，最多不超过2.5倍。

    6. 对于表格查询或需要多段落/多文档综合的问题，给予特别关注并提供更全面的回答。

    7. 如果上下文信息不足，可以进行合理推理，但要明确指出推理部分。

    8. 回答应简洁、准确、完整，直接解答问题，避免不必要的解释。

    9. 不要输出“检索到的文本块”、“根据”，“信息”等前缀修饰句，直接输出答案即可

    10. 不要使用"根据提供的信息"、"支撑信息显示"等前缀，直接给出答案。
    问题: {question}

    参考上下文：
    ···
    {context}
    ···

    请提供准确、相关且简洁的回答：""",
    Xunfei_PROMPT_TEMPLATE="""请结合参考的上下文内容回答用户问题，确保答案的准确性、全面性和权威性。如果上下文不能支撑用户问题，或者没有相关信息，请明确说明问题无法回答，避免生成虚假信息。
    只输出答案，不要输出额外内容，不要过多解释，不要输出额外无关文字以及过多修饰。

    如果给定的上下文无法让你做出回答，请直接回答：“无法回答。”，不要输出额外内容。

    问题: {question}
    可参考的上下文： 
    ··· 
    {context}
    ···
    简明准确的回答：
    """,

    Xunfei_PROMPT_TEMPLATE2="""请结合下面的资料，回答给定的问题：

    提问：{question}

    相关资料：{context}
    """,
    DF_PROMPT_TEMPLATE="""请结合参考的上下文内容回答用户问题，确保答案的准确性、全面性和权威性。如果上下文不能支撑用户问题，或者没有相关信息，请明确说明问题无法回答，避免生成虚假信息。
    只输出答案，尽量包括关键词，不要输出额外内容，不要过多解释，不要输出额外无关文字以及过多修饰。

    如果给定的上下文无法让你做出回答，请直接回答：“无法回答。”，不要输出额外内容。

    问题: {question}
    可参考的上下文： 
    ··· 
    {context}
    ···
    简明准确的回答：
    """,
    DF_PROMPT_TEMPLATE2="""
    系统提示：{system_prompt}

    支撑信息：{context}

    问题：{question}

    回答：""",
    DF_QWEN_PROMPT_TEMPLATE="""
        支撑信息：{context}

        问题：{question}

        回答：""",
    DF_QWEN_PROMPT_TEMPLATE2="""基于以下问题，从给定的文档中检索并抽取最相关的文本块：

    问题: {question}

    文档内容:
    {context}

    请按照以下指南进行检索和抽取：
    1. 识别并抽取包含问题答案的关键文本块。
    2. 如果答案分散在多个段落或需要整合多个信息，请提取所有相关文本块并按逻辑顺序组织。
    3. 对于表格数据，请完整提取包含答案的表格部分。
    4. 尽量保持原文表述，避免改写或总结。
    5. 确保提取的文本长度适中，理想情况下不超过原文相关部分的1.5倍。
    6. 只提取与问题直接相关的信息，避免包含无关内容。
    7. 不要输出“检索到的文本块”、“根据”，“信息”等前缀修饰句，直接输出答案即可
    8. 不要使用"根据提供的信息"、"支撑信息显示"等前缀，直接给出答案。
    请提供检索到的文本块：
    """
)


class BaseModel:
    def __init__(self, path: str = '') -> None:
        self.path = path

    def chat(self, prompt: str, history: List[dict], content: str) -> str:
        pass

    def load_model(self):
        pass


class OpenAIChat(BaseModel):
    def __init__(self, path: str = '', model: str = "gpt-3.5-turbo-1106") -> None:
        super().__init__(path)
        self.model = model

    def chat(self, prompt: str, history: List[dict], content: str) -> str:
        client = OpenAI()
        client.api_key = os.getenv("OPENAI_API_KEY")
        client.base_url = os.getenv("OPENAI_BASE_URL")
        history.append({'role': 'user',
                        'content': PROMPT_TEMPLATE['RAG_PROMPT_TEMPALTE'].format(question=prompt, context=content)})
        response = client.chat.completions.create(
            model=self.model,
            messages=history,
            max_tokens=150,
            temperature=0.1
        )
        return response.choices[0].message.content


class InternLMChat(BaseModel):
    def __init__(self, path: str = '') -> None:
        super().__init__(path)
        self.load_model()

    def chat(self, prompt: str, history: List = [], content: str = '') -> str:
        prompt = PROMPT_TEMPLATE['InternLM_PROMPT_TEMPALTE'].format(question=prompt, context=content)
        response, history = self.model.chat(self.tokenizer, prompt, history)
        return response

    def load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(self.path, torch_dtype=torch.float16,
                                                          trust_remote_code=True).cuda()


class GLMChat(BaseModel):
    def __init__(self, path: str = '') -> None:
        super().__init__(path)
        self.load_model()

    def chat(self, prompt: str, history=None, content: str = '', llm_only: bool = False) -> tuple[Any, Any]:
        if history is None:
            history = []
        if llm_only:
            prompt = prompt
        else:
            prompt = PROMPT_TEMPLATE['GLM_PROMPT_TEMPALTE'].format(question=prompt, context=content)
        response, history = self.model.chat(self.tokenizer, prompt, history, max_length=32000, num_beams=1,
                                            do_sample=True, top_p=0.8, temperature=0.2)
        return response, history

    def load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(self.path, torch_dtype=torch.float16,
                                                          trust_remote_code=True).cuda()


class GLM4Chat(BaseModel):
    def __init__(self, path: str = '') -> None:
        super().__init__(path)
        self.load_model()

    def chat(self, prompt: str, history=None, content: str = '', llm_only: bool = False) -> tuple[Any, Any]:
        if llm_only:
            prompt = prompt
        else:
            prompt = PROMPT_TEMPLATE['Qwen_PROMPT_TEMPALTE'].format(system_prompt=SYSTEM_PROMPT, question=prompt,
                                                                    context=content)
        prompt = prompt.encode("utf-8", 'ignore').decode('utf-8', 'ignore')
        print(prompt)

        inputs = self.tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                                                    add_generation_prompt=True,
                                                    tokenize=True,
                                                    return_tensors="pt",
                                                    return_dict=True
                                                    )

        inputs = inputs.to('cuda')
        gen_kwargs = {"max_length": 30000, "do_sample": False, "top_k": 10}
        with torch.no_grad():
            outputs = self.model.generate(**inputs, **gen_kwargs)
            outputs = outputs[:, inputs['input_ids'].shape[1]:]
            output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response, history = output, []
            return response, history

    def load_model(self):

        self.tokenizer = AutoTokenizer.from_pretrained(self.path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.path,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            trust_remote_code=True
        ).cuda().eval()


class QwenChat(BaseModel):
    def __init__(self, path: str = '') -> None:
        super().__init__(path)
        self.load_model()
        self.device = 'cuda'

    def chat(self, prompt: str, history: List = [], content: str = '', llm_only: bool = False) -> tuple[Any, Any]:
        if llm_only:
            prompt = prompt
        else:
            prompt = PROMPT_TEMPLATE['DF_QWEN_PROMPT_TEMPLATE2'].format(question=prompt, context=content)
        # print(prompt)
        messages = [
            {"role": "system", "content": "你是一个专门用于回答中国电信运营商相关问题的AI助手。"},
            {"role": "user", "content": prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        print(text)
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        generated_ids = self.model.generate(
            model_inputs.input_ids,
            max_new_tokens=1024,
            do_sample=False,
            top_k=10
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response, history

    def load_model(self):

        self.tokenizer = AutoTokenizer.from_pretrained(self.path, trust_remote_code=True)
        # self.model = AutoModelForCausalLM.from_pretrained(self.path, torch_dtype=torch.float16,
        #                                                   trust_remote_code=True).cuda()

        self.model = AutoModelForCausalLM.from_pretrained(
            self.path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        print("load model success")


class DashscopeChat(BaseModel):
    def __init__(self, path: str = '', model: str = "qwen-turbo") -> None:
        super().__init__(path)
        self.model = model

    def chat(self, prompt: str, history: List[Dict], content: str) -> str:
        import dashscope
        dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        history.append({'role': 'user',
                        'content': PROMPT_TEMPLATE['RAG_PROMPT_TEMPALTE'].format(question=prompt, context=content)})
        response = dashscope.Generation.call(
            model=self.model,
            messages=history,
            result_format='message',
            max_tokens=150,
            temperature=0.1
        )
        return response.output.choices[0].message.content


class ZhipuChat(BaseModel):
    def __init__(self, path: str = '', model: str = "glm-4") -> None:
        super().__init__(path)
        from zhipuai import ZhipuAI
        self.client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))
        self.model = model

    def chat(self, prompt: str, history: List[Dict], content: str) -> str:
        history.append({'role': 'user',
                        'content': PROMPT_TEMPLATE['RAG_PROMPT_TEMPALTE'].format(question=prompt, context=content)})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=history,
            max_tokens=150,
            temperature=0.1
        )
        return response.choices[0].message