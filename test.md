python -c "from fastembed import TextEmbedding; m=TextEmbedding(); v=list(m.embed(['P-101 pressure alarm']))[0]; print(len(v), v[:5])"
