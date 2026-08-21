PROJECTNAME = alertmanager-tg-sender-adapter
CURRENT = $(shell grep 'version = ' pyproject.toml | head -1 | sed 's/.*version = "\([^"]*\)".*/\1/')
TARGET = $(shell cat VERSION | sed 's/^v//')

release:
	sed -i 's/$(CURRENT)/$(TARGET)/g' README.md
	uv version $(TARGET)
	sed -i 's/$(CURRENT)/$(TARGET)/g' charts/$(PROJECTNAME)/Chart.yaml
	sed -i 's/$(CURRENT)/$(TARGET)/g' charts/$(PROJECTNAME)/README.md
	sed -i 's/$(CURRENT)/$(TARGET)/g' alertmanager_tg_sender_adapter/config.py