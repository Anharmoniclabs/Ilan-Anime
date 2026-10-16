"""Reference-grounded drawing: approved art -> editable cel layers -> measured round trip.

Extraction reuses ``studio.scan`` (ink + flat fills) and ``studio.layers`` (atlas
split). Nothing here invents subject geometry; every vector comes from source
pixels and every output records the source digest it came from.
"""
