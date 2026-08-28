from pathlib import Path


def test_storm_training_action_exists():
    workflow = Path('.github/workflows/train-storm-historical-ai-v31.yml')
    assert workflow.exists()
    text = workflow.read_text(encoding='utf-8')
    assert 'Train Storm Trajectory AI' in text
    assert 'scripts/38_download_historical_storm_data_v30.py' in text
    assert 'scripts/39_train_storm_historical_ai_v30.py' in text
    assert 'actions/upload-artifact@v4' in text


def test_storm_artifact_manifest_script_exists():
    script = Path('scripts/40_summarize_storm_training_artifacts_v31.py')
    assert script.exists()
    text = script.read_text(encoding='utf-8')
    assert 'storm_training_artifact_manifest_v31.json' in text
    assert 'historical_status' in text
    assert 'model_status' in text
