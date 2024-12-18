import gradio as gr
import json
import os
import re
import time
from typing import Dict, Tuple, Optional, Any
from generate import load_chat_model
from pydantic import BaseModel, ConfigDict
from jinja2 import Template
from typing_extensions import Literal
import yaml
from generate.chat_completion import ChatCompletionModel
from dotenv import load_dotenv
import logging
load_dotenv()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

EXAMPLES = [
    {
        "title": "Example 1: Basic Improvement",
        "prompt": "From the following list of Wikipedia article titles, identify which article this sentence came from.\nRespond with just the article title and nothing else.\n\nArticle titles:\n{{titles}}\n\nSentence to classify:\n{{sentence}}",
        "feedback": "The categories can only be: technology, culture, history, other."
    }
    # TODO: Add more examples here
]

class Prompt(BaseModel):
    name: str
    description: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    prompt: str
    format: Optional[Literal["fstring", "jinja2"]] = "fstring"
    model_config = ConfigDict(extra='allow')

    @classmethod
    def from_yaml(cls, yaml_string: str) -> 'Prompt':
        yaml_data = yaml.safe_load(yaml_string)
        return cls(**yaml_data)

    def render(self, context: Dict[str, Any] = {}) -> str:            
        if self.format == "jinja2":
            return self._render_jinja(context)
        else:
            return self._render_fstring(context)

    def _render_fstring(self, context: Dict[str, Any]) -> str:
        try:
            return eval(f"f'''{self.prompt}'''", context)
        except Exception as e:
            raise ValueError(f"Error rendering f-string: {e}")

    def _render_jinja(self, context: Dict[str, Any]) -> str:
        try:
            template = Template(self.prompt)
            return template.render(**context)
        except Exception as e:
            raise ValueError(f"Error rendering Jinja template: {e}")
        
    def get_extra_field(self, field_name: str, default: Any = None) -> Any:
        """Safely get an extra field with a default value if it doesn't exist."""
        return getattr(self, field_name, default)
    
def demo_card_click(e: gr.EventData):
    index = e._data['component']['index']
    return DEMO_LIST[index]['description']

def analyze_prompt(target_prompt: str, feedback: str, language: str, model: ChatCompletionModel) -> str:
    prompt_template = Prompt.from_yaml(open('./prompts/analyze_prompt.yaml', 'r').read())
    prompt = prompt_template.render({
        "prompt": target_prompt,
        "feedback": feedback,
        "language": language
    })
    output = model.generate(prompt, max_tokens=prompt_template.max_tokens, temperature=prompt_template.temperature)
    output = output.message.content
    logger.info(f"Prompt Analysis: {output}")
    report = re.findall(r"<report>(.*?)</report>", output, flags=re.DOTALL)[0]
    return report

def optimize_prompt(report: str, target_prompt: str, language: str, model: ChatCompletionModel) -> str:
    prompt_template = Prompt.from_yaml(open('./prompts/optimize_prompt.yaml', 'r').read())
    prompt = prompt_template.render({
        "report": report,
        "prompt": target_prompt,
        "language": language
    })
    output = model.generate(prompt, max_tokens=prompt_template.max_tokens, temperature=prompt_template.temperature)
    output = output.message.content
    logger.info(f"Prompt Result: {output}")
    return output

def process_analysis(target_prompt: str, feedback: str, language: str, model_id: str) -> Tuple[str, int]:
    """First step: Analyze the prompt and return the report"""
    model = load_chat_model(model_id)
    report = analyze_prompt(target_prompt, feedback, language, model)
    return report

def process_optimization(report: str, target_prompt: str, language: str, model_id: str) -> Tuple[str, int]:
    """Second step: Generate the optimized prompt based on the analysis"""
    model = load_chat_model(model_id)
    optimization = optimize_prompt(report, target_prompt, language, model)
    return optimization

def save_results(prompt: str, feedback: str, analysis: str, optimization: str, lang: str, model: str):
    data = {
        "original_prompt": prompt,
        "feedback": feedback,
        "analysis": analysis,
        "optimized_prompt": optimization,
        "language": lang,
        "model": model
    }
    
    # 时间戳文件名
    timestamp = time.strftime("%Y%m%d%H%M%S")
    temp_file = f"results_{timestamp}.json"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return temp_file

def update_api_key(key: str, value: str):
    """Update the API key environment variable"""
    if key and value:
        os.environ[key] = value
        logger.info(f"API key updated: {key}={value[:5]}...")

def fill_example(example_idx: int):
    """Auto-fill prompt and feedback with example content"""
    if 0 <= int(example_idx) < len(EXAMPLES):
        example = EXAMPLES[int(example_idx)]
        return example["prompt"], example["feedback"]
    return "", ""

with gr.Blocks() as demo:    
    with gr.Row():
        # Left Column
        with gr.Column(scale=1):
            with gr.Row():
                key_input = gr.Dropdown(
                    ["DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"],
                    label="API Key",
                )
                value_input = gr.Textbox(
                    show_label=True,
                    placeholder="Your API value...",
                    type="password",
                    label="API Value"
                )
                value_input.change(
                    fn=update_api_key,
                    inputs=[key_input, value_input],
                    outputs=[]
                )
            with gr.Row():
                language = gr.Dropdown(
                    choices=["中文", "English"],
                    value="中文",
                    label="Language/语言"
                )
                model = gr.Dropdown(
                    choices=["deepseek/deepseek-chat", "anthropic/claude-3-5-sonnet-latest", "openai/gpt-4o"],
                    value="deepseek/deepseek-chat",
                    label="Model/模型"
                )
            

            with gr.Row():            
                prompt_input = gr.Textbox(
                    label="Original Prompt/待优化的Prompt",
                    placeholder="Enter your prompt here...",
                    lines=5
                )
            with gr.Row():
                feedback_input = gr.Textbox(
                    label="Feedback/反馈",
                    placeholder="Enter your feedback here...",
                    lines=3
                )
            # Add example module
            with gr.Row():
                example_dropdown = gr.Dropdown(
                    choices=[(example["title"], i) for i, example in enumerate(EXAMPLES)],
                    label="Examples/示例",
                    value=None
                )
            # Add example auto-fill event
            example_dropdown.change(
                fn=fill_example,
                inputs=[example_dropdown],
                outputs=[prompt_input, feedback_input]
            )
            
            with gr.Row():
                submit_btn = gr.Button("Optimize")
                download_btn = gr.Button("Download")

        # Right Column
        with gr.Column(scale=1):
            analysis_output = gr.Textbox(
                label="Prompt Analysis",
                lines=10,
            )
            optimization_output = gr.Textbox(
                label="Optimized Prompt",
                lines=20,
            )
            copy_btn = gr.Button("Copy to Clipboard")

    # First submit handler for analysis
    submit_btn.click(
        fn=process_analysis,
        inputs=[prompt_input, feedback_input, language, model],
        outputs=analysis_output
    ).then(
        fn=process_optimization,
        inputs=[analysis_output, prompt_input, language, model],
        outputs=optimization_output
    )

    # Copy button handler
    copy_btn.click(
        fn=None,
        inputs=[optimization_output],
        outputs=None,
        js="(text) => {navigator.clipboard.writeText(text); return null;}"
    )

    download_btn.click(
        fn=save_results,
        inputs=[prompt_input, feedback_input, analysis_output, optimization_output, language, model],
        outputs=[
            gr.File(label="Download Results")
        ]
    )


if __name__ == "__main__":
    demo.launch(debug=True)
