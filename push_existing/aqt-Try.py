# -*- coding: utf-8 -*-

# This file is part of the Push Existing Vocab add-on for Anki
# Copyright: SpencerMAQ (Michael Spencer Quinto) <spencer.michael.q@gmail.com> 2017
# License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl-3.0.en.html

# NOTE: I've limited the number of replacements to 100 just so that this won't screw things just in case
# NOTE: This script unsuspends suspended cards as well but doesn't work for some vocabs like 爪楊枝, dunno why

from aqt.qt import *
from aqt import mw
from aqt.utils import showInfo          # TODO: temporary import
from anki.utils import intTime
# import csv
import os
import codecs
# import time                           # TODO: use anki utils intTime

from PyQt4 import QtCore

# Credits to Alex Yatskov (foosoft)
# I'm not even sure what this does
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

# from PyQt5.QtWidgets import *         # TODO: temporary import    =======
# from PyQt5.QtGui import *             # TODO: temporary import    =======
# from anki.storage import Collection

__version__ = '0.0'
# July 26 2017

HOTKEY = "Shift+P"


# ===================== TEMPORARY STUFF ===================== #
# ===================== TEMPORARY STUFF ===================== #
# just so I can get the namespaces inside  Collection
# manually typing them is very hard, and I'm very lazy
# TODO: comment out when porting

# class Temporary:
#     def __init__(self):
#         self.col = Collection('', log=True)
#
# mw = Temporary()

# ===================== TEMPORARY STUFF ===================== #
# ===================== TEMPORARY STUFF ===================== #


#  ===================== TO_DO_LIST ===================== #

# TODO: Include total count of vocab pasted
# TODO: total count of cards brought to front
# TODO: display number of cards that failed to be brought to front
# TODO: maybe this'd work better if you did by note type instead of deck? (or maybe both)
# TODO: display the vocabs that were found (and total number)
# TODO: display the vocabs that were NOT found (and total number)
# TODO: add functionality to tag the cards that were moved by adding tag: movedByPushToFrontPlugin
# TODO: drop-down menu of decks and note types
# TODO: drop-down menu of delimiter

# TODO: include functionaly for user to push only CERTAIN CARDS, not entire notes (DONE!)

# TODO: convert the vocab lists into sets to avoid rescheduling the same card twice

# TODO: (VERY IMPORTANT) Include a log file of the replacements done, number of replacements, what were not replaced, etc.

#  ===================== TO_DO_LIST ===================== #


class TextEditor(QDialog):
    def __init__(self, parent):
        """
        Initialize the UI
        :param parent:      global mw from aqt
        """

        # QDialog args from http://pyqt.sourceforge.net/Docs/PyQt4/qdialog.html#QDialog
        # __init__ (self, QWidget parent = None, Qt.WindowFlags flags = 0)
        super(TextEditor, self).__init__(parent)

        self.list_of_vocabs = []                                # list of mined vocab
        # self.list_of_deck_vocabs_20k = []                     # FIXME: Temp

        self.matched_vocab = []                                 # matched and rescheduled
        self.matchned_but_not_rescheduled = []
        self.unmatched_vocab = []
        # associated with a drop-down widget where the drop-down displays all decks and subdecks
        self.selected_deck = ''                                 # TODO: to be filled in by a signal
        self.selected_model = ''                                # TODO: to be filled in by a signal
        self.field_tomatch = ''                                 # TODO: to be filled in by a signal

        self.vocabulary_text = QPlainTextEdit(self)             # QTextEdit 1st arg = parent

        # ===================== BUTTONS ===================== #
        self.clr_btn = QPushButton('Clear Text')                # works
        self.resched_btn = QPushButton('Reschedule')
        # self.write_to_list_btn = QPushButton('Write to List') # FIXME: Probably unnecessary
        self.write_to_txt_btn = QPushButton('Write to CSV')
        self.import_btn = QPushButton('Import CSV')
        self.clear_list = QPushButton('Clear List')

        self.show_reschd_matched_cards = QPushButton('Show Rescheduled Matches')
        self.show_nonrschd_matched_cards = QPushButton('Show Matched but not Reschedued')
        self.show_unmatched_cards = QPushButton('Cards without any matches')

        # FIXME: temp button
        self.show_contents = QPushButton('Show Contents')
        self.write_deck_vocabs20k_to_CSV = QPushButton('Write Deck Vocabs to CSV')

        # ===================== SIGNALS ===================== #
        # self.write_to_list_btn.clicked.connect(self.write_to_list)
        self.resched_btn.clicked.connect(self.reschedule_cards_alternate)       # Main function
        # self.clr_btn.clicked.connect(self.clear_text)
        self.write_to_txt_btn.clicked.connect(self.csv_write)
        # TODO: add an additional LineEdit(or combobox) box where I can input what the delimiter will be
        self.import_btn.clicked.connect(lambda: self.import_csv(delimiter='\n'))
        self.show_contents.clicked.connect(self.show_contents_signal)
        self.clear_list.clicked.connect(self.reset_list)

        self.show_reschd_matched_cards.clicked.connect(self.show_rescheduled)
        self.show_nonrschd_matched_cards.clicked.connect(self.show_not_rescheduled)
        self.show_unmatched_cards.clicked.connect(self.show_not_matched)

        self.vocabulary_text.textChanged.connect(self.value_changed)

        # TODO: TEMP BUTTON
        # self.write_deck_vocabs20k_to_CSV.clicked.connect(self.write_deck_vocab_to_csv_method)

        # setWindowTitle is probably a super method from QtGui
        self.setWindowTitle('Push')

        self.init_ui()

    # FIXME: TEMPORARY
    # def write_deck_vocab_to_csv_method(self):
    #     filename = QFileDialog.getSaveFileName(self,
    #                                            'Save CSV',
    #                                            os.getenv('HOME'),
    #                                            'TXT(*.txt)'
    #                                            )
    #     if filename:
    #         if filename != '':
    #             with open(filename, 'w') as file:
    #
    #                 for _iter, line in enumerate(self.list_of_deck_vocabs_20k):
    #                     file.write(line.encode('utf-8'))
    #                     showInfo(_fromUtf8(line))
    #                     if _iter == 1:
    #                         break

    def init_ui(self):
        v_layout = QVBoxLayout()
        h_layout = QHBoxLayout()

        # buttons lined horizontally
        # to be added later to v_layout
        h_layout.addWidget(self.clr_btn)
        h_layout.addWidget(self.resched_btn)
        h_layout.addWidget(self.show_contents)
        # h_layout.addWidget(self.write_to_list_btn)                # FIXME: Temp
        h_layout.addWidget(self.write_to_txt_btn)                   # CSV Write
        h_layout.addWidget(self.import_btn)
        h_layout.addWidget(self.clear_list)

        h_layout.addWidget(self.show_reschd_matched_cards)
        h_layout.addWidget(self.show_nonrschd_matched_cards)
        h_layout.addWidget(self.show_unmatched_cards)

        # h_layout.addWidget(self.write_deck_vocabs20k_to_CSV)      # FIXME: Temp

        v_layout.addWidget(self.vocabulary_text)

        v_layout.addLayout(h_layout)

        self.setLayout(v_layout)

        self.show()

    # FIXME: doesn't fucking work
    def value_changed(self):
        self.list_of_vocabs[:] = []

        for line in self.vocabulary_text.toPlainText():
            self.list_of_vocabs.append(line)

    # temporary, only created this so that I'd see what the contents are
    def csv_write(self):
        filename = QFileDialog.getSaveFileName(self,
                                               'Save CSV',
                                               os.getenv('HOME'),
                                               'TXT(*.txt)'
                                               )

        if filename:
        # if filename != '':   # what does this do again?
            with open(filename, 'w') as file:
            # with open(filename, 'w', encoding='utf-8') as file:

                # csvwriter = csv.writer(file, delimiter='\n', quotechar='|')
                for line in self.list_of_vocabs:
                    file.write(line.encode('utf-8'))

    # TODO: Combobox for delimiter
    # TODO: use csv writer so I can specify the delimiter
    def import_csv(self, delimiter='\n'):
        del self.list_of_vocabs[:]

        # getOpenFileName (QWidget parent = None, QString caption = '',
        # QString directory = '', QString filter = '', Options options = 0)
        filename = QFileDialog.getOpenFileName(self,
                                               'Open CSV',
                                               os.getenv('HOME'),
                                               'TXT(*.csv *.txt)'
                                               )

        if filename:
            # if filename != '':   # what does this do again?
            with codecs.open(filename, 'r', encoding='utf-8') as file:

                # just did this because apparently the program doesn't resched the first vocab in the line
                self.list_of_vocabs.append('placeholder')
                # csvreader = csv.reader(file, delimiter=delimiter, quotechar='|')
                for line in file:
                    # line = line.decode('utf-8')
                    self.list_of_vocabs.append(line)

    # FIXME: obsolete!?
    # def write_to_list(self):
    #     self.list_of_vocabs[:] = []
    #
    #     for line in self.vocabulary_text.toPlainText():
    #         self.list_of_vocabs.append(line)

    #
    def show_contents_signal(self):
        for vocab in self.list_of_vocabs:
            showInfo(_fromUtf8(vocab))

    # works
    def clear_text(self):
        self.vocabulary_text.clear()
        self.vocabulary_text.setText('')

    def reset_list(self):
        self.list_of_vocabs[:] = []

    def show_rescheduled(self):
        for matched in self.matched_vocab:
            showInfo(_fromUtf8(matched))

    def show_not_rescheduled(self):
        for matched_but_not_res in self.matchned_but_not_rescheduled:
            showInfo(_fromUtf8(matched_but_not_res))

    def show_not_matched(self):
        for unmatched in self.unmatched_vocab:
            showInfo(_fromUtf8(unmatched))

    # NOTE: this seems to be slower than my original function
    # might need to recode this
    # TODO: I might recode this to use executemany instead, I doubt that'll speed things up though

    # FIXME: (VERY IMPORTANT!!!) it appears that the first vocab on the list is not rescheduled (wheter suspended or not)
    # it appears that the fix is simply to add a newline at the beginning of the list
    def reschedule_cards_alternate(self):
        """
        Main function of the program
        Checks every Note > Field if it is inside the
        list of mined words and sets the due date to zero accdngly
        :return:    None
        """

        # TODO: Use a combobox for the model instead of this primitive shit
        self.field_tomatch = 'Expression_Original_Unedited'
        self.selected_model = 'Japanese-1b811 example_sentences'

        # TODO: Add a Push Button for this
        self.number_of_replacements = 0

        mid = mw.col.models.byName(self.selected_model)['id']       # model ID
        nids = mw.col.findNotes('mid:' + str(mid))                  # returns a list of noteIds

        ctr = 0

        # list comprehension of tuples in format: nid, first field for that nid (reversed)
        # TODO: how to ensure that all html is stripped? Is there a module for that? (beautifulsoup perhaps?)
        dict_of_note_first_fields = {mw.col.getNote(note_id)[self.field_tomatch].strip().strip('<span>').strip('</span>') :
                                        note_id
                                        for note_id in nids}

        list_of_deck_vocabs_20k = dict_of_note_first_fields.keys()
        list_of_vocabs = [_fromUtf8(vocab) for vocab in self.list_of_vocabs]

        # ===== TEMP ==== #
        # taka_nid = dict_of_note_first_fields[u'爪楊枝']
        # cidssss = mw.col.findCards('nid:' + str(taka_nid))
        # try:
        #     firrsssttcarddiddd = cidssss[0]
        # except IndexError:
        #     firrsssttcarddiddd = cidssss
        #
        # card = mw.col.getCard(firrsssttcarddiddd)
        #
        # showInfo(str(card.queue))
        # return

        # NOTE: card.queue for 爪楊枝 == -1

        # booooool = u'爪楊枝' in list_of_deck_vocabs_20k
        # showInfo(str(booooool))
        # # booooool was shown to return TRUE
        # return
        # ===== TEMP ==== #

        for vocab in list_of_vocabs:
            if vocab.strip() in list_of_deck_vocabs_20k and vocab != 'placeholder':

                # ===== TEMP ==== #
                # if vocab.strip() == u'曇る':
                #     showInfo('herhehehe')
                #     break
                # ===== TEMP ==== #

                # showInfo(_fromUtf8(vocab))
                nid = dict_of_note_first_fields[_fromUtf8(vocab.strip())]
                cids = mw.col.findCards('nid:' + str(nid))

                # FIXME: Probably uncessary, only did this because of a prev bug
                try:
                    first_card_id = cids[0]
                except IndexError:
                    first_card_id = cids

                card = mw.col.getCard(first_card_id)

                # FIXME: this if might not be needed, the if next to this might be the only needed clause
                # since type = queue essentially
                if card.type == 0:
                    self.matched_vocab.append(vocab)
                    ctr += 1
                    self.number_of_replacements += 1

                    # NOTE: You can't use LIMIT inside this SQL operation because they only execute one at a time
                    mw.col.db.execute(''' UPDATE cards
                                            SET due = ?,
                                                mod = ?,
                                                usn = -1
                                            WHERE
                                                id = ?
                                                    AND
                                                type = 0
                                        ''',
                                            ctr,
                                            intTime(),
                                            int(first_card_id)
                                      )

                # Same as type, but -1=suspended, -2=user buried, -3=sched buried
                if card.queue == -1 or card.queue == -2 or card.queue == -3:
                    # showInfo(_fromUtf8(vocab))
                    self.matched_vocab.append(vocab)
                    ctr += 1
                    self.number_of_replacements += 1

                    # type = 0 unsuspends the card
                    mw.col.db.execute(''' UPDATE cards
                                            SET due = ?,
                                                mod = ?,
                                                usn = -1,
                                                type = 0,
                                                queue = 0
                                            WHERE
                                                id = ?
                                        ''',
                                            ctr,
                                            intTime(),
                                            int(first_card_id)
                                      )

                # elif card.queue != -1:
                #     self.matchned_but_not_rescheduled.append(vocab)

                elif card.type != 0:
                    # cards that weren't rescheduled because they're learning/mature
                    self.matchned_but_not_rescheduled.append(vocab)

                # showInfo(str(type(card.queue)))

                # NOTE: Limit the number of reschedules to 100 for now
                # break when the number of replacements is the same as the list length
                if ctr == 2*len(list_of_vocabs) + 1:
                # if ctr == 100:
                    break

            else:
                self.unmatched_vocab.append(vocab)

        mw.reset()


    # MAIN
    # def reschedule_cards(self):
    #     """
    #     Main function of the program
    #     Checks every Note > Field if it is inside the
    #     list of mined words and sets the due date to zero accdngly
    #     :return:    None
    #     """
    #     # did = mw.col.decks.id("")
    #     # print(dir(mw.col.decks.id("")))
    #     # deck = mw.col.decks.byName("")
    #
    #     # FIXME: recode this entire function such that you only check for
    #     # each vocab if they are in the collection
    #     # i.e. for vocab in list of vocabs
    #
    #     self.field_tomatch = 'Expression_Original_Unedited'
    #     self.selected_model = 'Japanese-1b811 example_sentences'
    #
    #     self.number_of_replacements = 0
    #
    #     mid = mw.col.models.byName(self.selected_model)['id']
    #     nids = mw.col.findNotes('mid:' + str(mid))
    #
    #     ctr = 0
    #     for note_id in nids:
    #         note = mw.col.getNote(note_id)
    #         # field to match:
    #         # note[self.field_tomatch]
    #
    #         # list_of_vocabs = [i.encode('utf-8') for i in self.list_of_vocabs]
    #         list_of_vocabs = [_fromUtf8(vocab) for vocab in self.list_of_vocabs]
    #
    #         # note[self.field_tomatch] is unicode OK
    #
    #         # if unicode(note[self.field_tomatch], 'utf-8') in list_of_vocabs:
    #         # note_first_field = note[self.field_tomatch]
    #
    #         if note[self.field_tomatch] in list_of_vocabs:
    #
    #             # note is a dictionary containing all the fields
    #             # Note that from common sense, the Notes themselves
    #             # won't have due values because it is the cards that
    #             # are supposed to be studied
    #             cids = mw.col.findCards('nid:' + str(note_id))
    #             first_card_id = cids[0]
    #             # cids = card IDs (if there is more than one card)
    #
    #             card = mw.col.getCard(first_card_id)
    #
    #             # https://github.com/ankidroid/Anki-Android/wiki/Database-Structure
    #             # 0=new, 1=learning, 2=due
    #             # reschedule should be limited only to new cards, don't touch learning and due cards
    #             if card.type == 0:
    #                 # just for checking purposes, i.e. place the names of the rescheduled cards in a list
    #                 self.matched_vocab.append(note[self.field_tomatch])
    #                 # reschedule card
    #                 card.due = 0
    #                 ctr += 1
    #                 self.number_of_replacements += 1
    #
    #                 mw.col.db.execute(  ''' UPDATE cards
    #                                         SET due = ?,
    #                                             mod = ?,
    #                                             usn = -1
    #                                         WHERE
    #                                             id = ? AND
    #                                             type = 0
    #                                     ''', ctr, time.time(), first_card_id
    #                                     )
    #
    #                 '''
    #                 IMPORTANT NOTE TO SELF:
    #                 doing things like card.due = 0 doesn't work because
    #                 It doesn't tap into the database
    #                 '''
    #
    #             elif card.queue == -1:
    #                 # just for checking purposes, i.e. place the names of the rescheduled cards in a list
    #                 self.matched_vocab.append(note[self.field_tomatch])
    #                 # reschedule card
    #                 card.due = 0
    #                 ctr += 1
    #                 self.number_of_replacements += 1
    #
    #                 mw.col.db.execute(  ''' UPDATE cards
    #                                         SET due = ?,
    #                                             mod = ?,
    #                                             usn = -1
    #                                             type = 0
    #                                         WHERE
    #                                             id = ? AND
    #                                             type = 0
    #                                     ''', ctr, time.time(), first_card_id
    #                                     )
    #             elif card.queue != -1:
    #                 self.matchned_but_not_rescheduled.append(note[self.field_tomatch])
    #
    #             elif card.type != 0:
    #                 # cards that weren't rescheduled because they're learning/mature
    #                 self.matchned_but_not_rescheduled.append(note[self.field_tomatch])
    #
    #         # else:
    #             # FIXME: this adds the wrong vocab (every vocab from the 20k+ vocab
    #             # self.unmatched_vocab.append(note[self.field_tomatch])
    #
    #     # pycharm can't detect reset
    #     mw.reset()
    #     '''
    #     ------from anki/find.py------
    #             def findCards(self, query, order=False):
    #                 "Return a list of card ids for QUERY."
    #
    #     '''


def init_window():
    mw.texteditor = TextEditor(mw)

run_action = QAction('Push Existing Vocabulary', mw)
run_action.setShortcut(QKeySequence(HOTKEY))
run_action.triggered.connect(init_window)

mw.form.menuTools.addAction(run_action)

# ## I might need to use SQLITE for changing the due value of the said cards
# ## and unsuspend them simultaneously
# TODO: vvv What's that?
# https://www.python.org/dev/peps/pep-0350/
