# Contributing to SpectralBridge

Thanks for your interest in improving SpectralBridge! This project is built to be
clear, tested, and easy to run locally.

## Getting started

```bash
git clone https://github.com/<your-username>/spectralbridge.git
cd spectralbridge

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

See [`README.md`](./README.md) for the full local-run guide.

## Development workflow

1. Fork & branch from `main`:
   ```bash
   git checkout -b feat/your-feature
   ```
2. Make your changes. Keep commits focused.
3. **Before pushing**, verify locally:
   ```bash
   cd backend && pytest -q        # tests must pass
   cd ../frontend && npm run build # frontend must build
   ```
4. Push and open a Pull Request against `main`. Fill in the PR template.

## Code style

- Python: PEP 8, type hints, no inline debug prints.
- TypeScript/React: strict mode, functional components, Tailwind classes only
  (no inline `style` unless animating).
- No comments unless a non-obvious decision needs explaining (the codebase
  documents its *why* in docstrings and the README).

## Areas that welcome contributions

- Improving cross-platform tag normalization (`backend/app/ml/preprocessing.py`).
- Tightening the bridge filter / diversity logic (`backend/app/ml/recommender.py`).
- UI polish and accessibility (`frontend/src/components/`).
- More tests in `backend/tests/`.

## Reporting issues

Use the issue templates (Bug report / Feature request). Include the input URL,
expected vs. actual output, and your environment.
