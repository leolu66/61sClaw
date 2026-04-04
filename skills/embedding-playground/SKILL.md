# Embedding Playground

A web tool for experimenting with different embedding models.

## Trigger Words
- embedding playground
- vector experiment
- embedding test

## Start Command
node server.js

## Port
19876

## Display
canvas present

## Features
1. Model Management - 8 preset models + custom models
2. Vector Generation - Generate embeddings with multiple models
3. Dimension Comparison - Compare first 10 dimensions
4. Similarity Analysis - Cosine similarity matrix with heatmap
5. Visualization - PCA 2D/3D scatter plots with Plotly

## Files
- server.js - HTTP server
- db.js - JSON database
- embedder.js - Embedding API client
- calculator.js - Vector calculations
- visualizer.js - PCA and charts
- index.html - Frontend
- references/preset-models.json - Preset model configs
