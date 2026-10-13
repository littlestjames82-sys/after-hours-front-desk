# Sandbox environment for the After-Hours Front Desk demo.
# Source this, then run desk/server.py or smoke_test.py.
export AHFD_LLAMA_SERVER="${AHFD_LLAMA_SERVER:-$HOME/workspace/ghost-os/spike-llama/src/build/bin/llama-server}"
export AHFD_LLAMA_CLI="${AHFD_LLAMA_CLI:-$HOME/workspace/ghost-os/spike-llama/src/build/bin/llama-cli}"
export AHFD_MODEL="${AHFD_MODEL:-$HOME/workspace/downloads/gemma-3-4b-it-Q4_K_M.gguf}"
export AHFD_BRAIN_URL="${AHFD_BRAIN_URL:-http://127.0.0.1:8771}"
export AHFD_SOPRO_URL="${AHFD_SOPRO_URL:-http://127.0.0.1:8766}"
export AHFD_SOPRO_SERVER="${AHFD_SOPRO_SERVER:-$HOME/workspace/sopro-test/server.py}"
export AHFD_SOPRO_PYTHON="${AHFD_SOPRO_PYTHON:-$HOME/workspace/sopro-test/.venv/bin/python}"
export AHFD_SOPRO_CLI="${AHFD_SOPRO_CLI:-$HOME/workspace/sopro-test/.venv/bin/soprotts}"
export AHFD_SOPRO_MODEL="${AHFD_SOPRO_MODEL:-$HOME/workspace/sopro-test/model}"
export AHFD_SOPRO_REF="${AHFD_SOPRO_REF:-$HOME/workspace/sopro-test/ref.wav}"
export AHFD_PORT="${AHFD_PORT:-8890}"
