CURRENT = 1.1.1
TARGET = 1.1.2
PROJECTNAME = $(shell basename "$(PWD)")

release:
	sed -i '' 's/$(CURRENT)/$(TARGET)/g' VERSION
	sed -i '' 's/$(CURRENT)/$(TARGET)/g' README.md
	uv version $(TARGET)
	sed -i '' 's/$(CURRENT)/$(TARGET)/g' charts/$(PROJECTNAME)/Chart.yaml
	rm -f charts/$(PROJECTNAME)/$(PROJECTNAME)-$(CURRENT).tgz
	helm-docs .
	helm package charts/$(PROJECTNAME) -d charts/$(PROJECTNAME)/