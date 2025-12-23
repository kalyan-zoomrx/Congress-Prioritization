from prioritization.pipelines.langgraph_pipeline import create_prioritization_pipeline

pipeline = create_prioritization_pipeline()
result = pipeline.invoke({
    "directory": "data/test01_ASCO_2025_RevMed/",
    "model": "gpt-4.1",
    "iteration_count": 0,
    "validation_errors": []
})

print(f"Workflow finished: {result['output_file']}")