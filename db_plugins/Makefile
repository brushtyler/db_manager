UI_SOURCES=$(wildcard */ui/*.ui)
UI_FILES=$(patsubst %.ui,%_ui.py,$(UI_SOURCES))

RC_SOURCES=$(wildcard */*.qrc)
RC_FILES=$(patsubst %.qrc,%_rc.py,$(RC_SOURCES))

GEN_FILES = ${UI_FILES} ${RC_FILES}

all: $(GEN_FILES)
ui: $(UI_FILES)
resources: $(RC_FILES)

$(UI_FILES): %_ui.py: %.ui
	pyuic4 -o $@ $< || return 0
	
$(RC_FILES): %_rc.py: %.qrc
	pyrcc4 -o $@ $< || return 0


clean:
	rm -f $(GEN_FILES) *.pyc
