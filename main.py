from prioritization.pipelines.supervisor import parsing_pipeline, analysis_pipeline

TEST_DIRECTORY = "data/test02_ERA_2025_Calliditas/"
#MODEL = "gpt-4.1"
MODEL = "gemini/gemini-2.5-pro"
#MODEL = "claude-haiku-4-5"

if __name__ == "__main__":
    analysis_pipeline(directory=TEST_DIRECTORY, model=MODEL)
    parsing_pipeline(directory=TEST_DIRECTORY, model=MODEL)
