# VideoDB pSEO pipeline — see README.md for the full loop.
# Secrets come from the environment: SEMRUSH_KEY, KIE_API_KEY (never committed).

.PHONY: keywords build images benchmark deploy serve all

keywords:            ## discover + score keywords, emit article briefs (needs SEMRUSH_KEY)
	python3 find_keywords.py

build:               ## charts -> pages -> listing (fully offline)
	python3 make_charts.py && python3 build_html.py && python3 make_listing.py

images:              ## generate missing hero images via kie.ai (needs KIE_API_KEY)
	python3 gen_images.py

benchmark:           ## check live SERP position for every published article (needs SEMRUSH_KEY)
	python3 benchmark.py

deploy: build        ## rebuild, commit, push (GitHub Pages serves main:/docs)
	git add -A && git commit -m "Publish: rebuild pages" && git push

serve:               ## preview the built site locally
	cd docs && python3 -m http.server 8931

all: keywords build
