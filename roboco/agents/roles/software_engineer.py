class SoftwareEngineerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name='SWE-01',
            role='software_engineer',
            capabilities=['code_generation', 'debugging', 'system_optimization'],
            system_prompt='''Specialized in robotic control systems and API development.
            Prioritize modular, testable code with proper documentation.'''
        )
        self.current_task = None

    def review_code(self, codeblock):
        '''Analyze code for quality and safety'''
        # Implementation using AST analysis
        {{ ... }}
