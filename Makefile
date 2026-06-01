CURRENT = 1.0.5
TARGET = 1.0.6
PROJECTNAME = $(shell basename "$(PWD)")

release:
	sed -i '' 's/$(CURRENT)/$(TARGET)/g' VERSION
	sed -i '' 's/$(CURRENT)/$(TARGET)/g' README.md
	uv version $(TARGET)
	sed -i '' 's/$(CURRENT)/$(TARGET)/g' charts/$(PROJECTNAME)/Chart.yaml
	rm -f charts/$(PROJECTNAME)/$(PROJECTNAME)-$(CURRENT).tgz
	helm-docs .
	helm package charts/$(PROJECTNAME) -d charts/$(PROJECTNAME)/