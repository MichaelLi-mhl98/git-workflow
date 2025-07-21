import re
from typing import List

def extract_user_prompts(chat_text: str) -> List[str]:
    """
    Extract user prompts from chat history.
    Each user prompt is exactly one line starting with a timestamp.
    
    Args:
        chat_text: The full chat history text
        
    Returns:
        List of user prompts with timestamps
    """
    
    # Split text into lines
    lines = chat_text.strip().split('\n')
    
    prompts = []
    
    for line in lines:
        line = line.strip()
        
        # Check if line starts with timestamp pattern (MM/DD/YYYY HH:MM:SS :)
        timestamp_match = re.match(r'^(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s*:\s*)(.*)', line)
        
        if timestamp_match:
            # Extract the full line (timestamp + prompt)
            prompts.append(line)
    
    return prompts

def extract_prompts_only(chat_text: str) -> List[str]:
    """
    Extract just the prompt text without timestamps.
    
    Args:
        chat_text: The full chat history text
        
    Returns:
        List of prompt texts only
    """
    
    # Split text into lines
    lines = chat_text.strip().split('\n')
    
    prompt_texts = []
    
    for line in lines:
        line = line.strip()
        
        # Check if line starts with timestamp pattern and extract just the prompt part
        timestamp_match = re.match(r'^(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s*:\s*)(.*)', line)
        
        if timestamp_match:
            prompt_text = timestamp_match.group(2).strip()
            if prompt_text:
                prompt_texts.append(prompt_text)
    
    return prompt_texts

class ChatPromptExtractor:
    def __init__(self, file_path: str = None, chat_text: str = None):
        """
        Initialize the extractor with either a file path or chat text.
        
        Args:
            file_path: Path to the chat history file
            chat_text: Direct chat history text
        """
        self.file_path = file_path
        self.chat_text = chat_text
        
        if file_path and not chat_text:
            self.load_from_file()

    def load_from_file(self):
        """Load chat history from file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                self.chat_text = file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Chat file not found: {self.file_path}")

    def extract_prompts_with_timestamps(self) -> List[str]:
        """Extract prompts with their timestamps."""
        if not self.chat_text:
            raise ValueError("No chat data loaded.")
        return extract_user_prompts(self.chat_text)

    def extract_prompts_only(self) -> List[str]:
        """Extract just the prompt texts without timestamps."""
        if not self.chat_text:
            raise ValueError("No chat data loaded.")
        return extract_prompts_only(self.chat_text)

    def get_unique_prompts(self) -> List[str]:
        """Get unique prompt texts, maintaining chronological order."""
        prompts = self.extract_prompts_only()
        seen = set()
        unique_prompts = []
        
        for text in prompts:
            text = text.strip()
            if text not in seen:
                seen.add(text)
                unique_prompts.append(text)
        
        return unique_prompts

    def save_prompts_to_file(self, output_file: str, include_timestamps: bool = True):
        """Save extracted prompts to a text file."""
        if include_timestamps:
            prompts = self.extract_prompts_with_timestamps()
        else:
            prompts = self.extract_prompts_only()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Extracted User Prompts from Chat History\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total prompts found: {len(prompts)}\n\n")
            
            for i, prompt in enumerate(prompts, 1):
                f.write(f"{i}. {prompt}\n\n")

# Example usage
if __name__ == "__main__":
    # Method 1: Using file path
    extractor = ChatPromptExtractor("paste.txt")
    
    # Method 2: Using direct text
    # extractor = ChatPromptExtractor(chat_text=your_chat_text)
    
    # Extract prompts
    prompts_with_timestamps = extractor.extract_prompts_with_timestamps()
    prompts_only = extractor.extract_prompts_only()
    unique_prompts = extractor.get_unique_prompts()
    
    # Display results
    print("=== USER PROMPTS WITH TIMESTAMPS ===")
    for i, prompt in enumerate(prompts_with_timestamps, 1):
        print(f"{i}. {prompt}")
        print()
    
    print("\n=== PROMPT TEXTS ONLY ===")
    for i, prompt in enumerate(prompts_only, 1):
        print(f"{i}. {prompt}")
        print()
    
    # Save to file with timestamps (default)
    extractor.save_prompts_to_file("extracted_user_prompts_with_timestamps.txt", include_timestamps=True)
    
    # Or save without timestamps
    extractor.save_prompts_to_file("extracted_user_prompts_only.txt", include_timestamps=False)
    
    print(f"\nExtracted {len(prompts_only)} user prompts:")
    print("- Saved with timestamps to 'extracted_user_prompts_with_timestamps.txt'")
    print("- Saved without timestamps to 'extracted_user_prompts_only.txt'")