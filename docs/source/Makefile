outdir := html

doc:
	python -m sphinx -T -E -b html -d _build/doctrees -D language=en ./ $(outdir)

clean:
	rm -rf $(outdir) generated _build

all: clean doc