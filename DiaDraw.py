import sys
import itertools
#print "This is the name of the script: ", sys.argv[0]
#print "Number of arguments: ", len(sys.argv)
#print "The arguments are: " , str(sys.argv)

use_circle_of_fifths = True
includeArpeggios = True
includeBackupArpeggiosOnly = True
UNIQUE_NOTES_MODE = True
IncludeAllOutput = False

colours = ("-fill \"rgb(255,155,200)\"",
		   "-fill \"rgb(255,200,155)\"",
		   "-fill \"rgb(200,255,200)\"",
		   "-fill \"rgb(200,200,255)\"",
		   "-fill \"rgb(155,200,255)\"",
		   "-fill \"rgb(200,155,255)\"",
		   "-fill \"rgb(155,255,200)\"")

##### Semitone Math:
semitones = [
"A",
"A#",
"B",
"C",
"C#",
"D",
"D#",
"E",
"F",
"F#",
"G",
"G#"
]

# Notes that are the same as one another:
equivilents = {
'F#': 'Gb',
'Gb': 'F#',
'G#': 'Ab',
'Ab': 'G#',
'A#': 'Bb',
'Bb': 'A#',
'C#': 'Db',
'Db': 'C#',
'D#': 'Eb',
'Eb': 'D#'
}

semitone_lookup = {}
i = 0
for tone in semitones:
	semitone_lookup[tone] = i
	if tone in equivilents:
		semitone_lookup[equivilents[tone]] = i
	i += 1

def create_circle_of_fifths(start_point):
	o = []
	end = start_point
	first = 1
	while (end != start_point or first):
		first = 0
		low = len(o) < 6
		add_note = semitones[start_point]
		if low and add_note in equivilents:
			add_note = equivilents[add_note]
		o.append(add_note)
		start_point = (start_point + 7) % 12
	return o

class Note:
	def __init__(self, musical_note, press, row_index, button_index):
		self.note = musical_note
		spl = self.NoteSplit(musical_note)
		self.basic = spl[0]
		self.octave = int(spl[1])
		self.isPress = press

		self.all_basics = [self.basic]
		if self.basic in equivilents:
			equiv_note = equivilents[self.basic]
			self.all_basics.append(equiv_note)

		# Generate an absolute value that correspondes to this musical tone:
		semitone_score = semitone_lookup[spl[0]]
		if semitone_score < semitone_lookup["C"]:
			semitone_score += 12
		semitone_score += int(spl[1]) * 12

		self.score = semitone_score

		self.row_index = int(row_index)
		self.button_index = int(button_index) / 2
		self.unique = row_index * 100 + button_index

	def Key(self):
		return self.score

	def __str__(self):
		return self.note + " " + str(self.unique)
	def __repr__(self):
		if self.isPress:
			return self.note + "+"
		else:
			return self.note + "-"

	def NoteMatch(self,other):
		return self.score == other.score

	def __eq__(self, other):
		# use a semitone score comparison:
		return self.unique == other.unique
	def __lt__(self, other):
		# Use the semitone score when sorting, too
		return self.score < other.score
	def __hash__(self):
		return self.unique

	def NoteSplit(self, note):
		# This splits A5 into (A, 5)
		note_name = note.rstrip("0123456789")
		octave = note[len(note_name):]
		return (note_name, octave)

class Layout:
	def __init__(self):
		self.rows = []
		self.raw_rows = []
		self.notes = []
		self.chords = []
		self.row_count = 0

	def __str__(self):
		return str("Diatonic layout with %d rows and %d buttons" % (len(self.raw_rows), len(self.notes) / 2) )
	def __repr__(self):
		return str(self.notes)

	def CompareNote(note1, note2):
		if note1[0] == note2[0]:
			return True
		return False

	def CompareNoteSameDirection(note1, note2):
		if CompareNote(note1,note2):
			if note1[4] == note2[4]:
				return True

		return False

	def AddRow(self, r):
		# Row list is expected to be a stream of PUSH PULL notes from low to high

		self.raw_rows.append(r)
		

		# Generate a list of notes.
		# This is a list of tuples in the format (N#, N, #, isPush)
		# Start on a push:
		push = True
		for n in range(len(r)):
			self.notes.append( Note(r[n], push, self.row_count, n) )
			# Maybe I should use a dictionary?
			#self.notes.append( (r[n], t[0], int(t[1]), semitone_score, push, (self.row_count, n) ) ) 
			push = not push

		self.row_count += 1
		self.notes.sort()

	def BuildChords(self, chord_list):
		# This method will build a list of all the chords
		# that the instrument includes the notes for, as well as include each one of those note structures in
		# a list


		# I need to handle notes that appear on multiple buttons at once
		dddebug = False
		for name, makeup in chord_list:
			# For each Chord Name, examine the CSV note makeup. The prefered inversion is assumed from the order of the notes
			# in the layout.
			l = makeup.split(",")

			# We will generate a dictionary of all the notes in the chord, keyed to the basic note that this is/
			# We will also generate a list of all the notes that are involved just in a pile, as this is helpful for
			# keeping track of buttons that aren't part of a full preferred inversion (Eg you have 3 Cs but 2 Gs)
			notes_in_chord = {}
			loose_notes = {"PUSH": [], "PULL": [], "ARP": []}
			for n in self.notes:
				basic = n.basic
				if basic in l:
					# if the basic note is in the chord
					# Add this note to the list of this note:
					if basic in notes_in_chord:
						notes_in_chord[basic].append(n)
					else:
						o = []
						o.append(n)
						notes_in_chord[basic] = o

					loose_notes["ARP"].append(n)
					if n.isPress:
						loose_notes["PUSH"].append(n)
					else:
						loose_notes["PULL"].append(n)

			# notes_in_chord now contains all notes that we have, push or pull, that are in this chord
			# Let's built every single combination of this chord and score them:

			fixed_structure = []
			for a in l:
				fixed_structure.append(notes_in_chord[a])

			all_permutes = list(itertools.product(*fixed_structure))

			scored_permutes = []
			for perm in all_permutes:
				scored_permutes.append( [0, "unknown", perm] )

			#print scored_permutes

			# All permutes now contains every permutation of the chord. Now, let's score all of these results and pick the best one
			# After that we shall remove these notes as options, and then find the next best chord

			def score_chords(chords):
				for schord in chords:
					score = 0
					chord = schord[2]
					root_note = chord[0]

					# Step one: the lower the root note, the higher the score:
					base = root_note.score
					score += 100 - base

					z = "PULL"

					for n in chord:
						nsc = n.score
						if nsc < base:
							score -= 50

						dist = abs(base - nsc)
						# the closer the note is to the root note, the better:
						score -= dist

						# if the direction is mixed, remove a lot of points
						if z == "PULL" and n.isPress:
							z = "PUSH"

						if n.isPress != root_note.isPress and z != "ARP":
							score -= 1000
							z = "ARP"

					schord[1] = z
					schord[0] = score
					#print schord

			score_chords(scored_permutes)
			scored_permutes.sort()#(key = lambda x: x[0])

			if not includeArpeggios:
				replacement = []
				for x in range(len(scored_permutes)):
					if not scored_permutes[x][1] == "ARP":
						replacement.append(scored_permutes[x])

				scored_permutes = replacement

			#for test in scored_permutes:
			#	print test

			#print "Beginning best chord selection for %s." % (name)
			dddebug = False
			chord_results = []

			loop_protection = 0
			while len(scored_permutes) > 0 and loop_protection < 50:
				best_chord = scored_permutes[-1]
				chord_results.append(best_chord)
				if dddebug:
					print "Best chord: " + str(best_chord)
					print "There are %d records" % (len(scored_permutes))
				next_list = []

				best_score = best_chord[0]
				best_typ = best_chord[1]
				best_notes = best_chord[2]

				# we know the best chord
				# We do have duplicate notes, maybe we shouldn't include them?
				for note in best_notes:
					#for key in loose_notes.keys():
					if note in loose_notes[best_typ]:
						loose_notes[best_typ].remove(note)

				for a, t, prev_result in scored_permutes:
					exclude = 0
					# We scan through all our permutations and remove any that include this button
					# this however specifically represents a unique button, rather than a given pitch, eg C#5
					# However, If this isn't an arpeggio chord, we should not remove appreggio chords:

					for note in prev_result:
						if UNIQUE_NOTES_MODE:
							for other_note in best_notes:
								if note.NoteMatch(other_note):
									exclude += 1
						else:
							if note in best_notes:
								exclude += 1	

					if best_typ != "ARP" and t == "ARP":
						exclude = 0

					if exclude == 0:
						next_list.append([a,t,prev_result])
				
				if dddebug:
					print "There are now %d records" % (len(next_list))
					
				#score_chords(next_list)
				next_list.sort()
				scored_permutes = next_list

				loop_protection += 1

			#for test in chord_results:
				#print test

			#print loose_notes

			self.chords.append( ( (name, makeup), chord_results, loose_notes) )

		return False

	def FindChordNotes(self, chord):

		return False

	def DrawLayout(self):

		# Calculates the height of our output:
		maxlen = 0
		for row in self.raw_rows:
			maxlen = max(maxlen, len(row) / 2)
		self.width = maxlen * (distance_x) + 2 * x_border

		# Height should be, the borders on top, the total distance betwen the top of the top row and the top of the bottom row, and then
		# a single width of a circle
		self.height = y_border * 2 + (self.row_count - 1) * distance_y + circle_size

		half_circle = circle_size * 0.5
		# The starting height will be the border plus half of a circle
		row_base_height = y_border + half_circle

		# Calculate center position for text:
		center_x = self.width / 2
		center_y = self.height / 2

		# Set up the layout drawing:
		layout_output = "convert -size %sx%s xc:transparent -fill transparent -strokewidth 2  -stroke black" % (self.width, self.height)
		text_extra = " -fill black -font Arial -stroke transparent -pointsize 36 -gravity center"
		text_small = " -pointsize 24"

		self.arc_lookup = {}

		# for each row, we will draw all the buttons and lines:
		buttons_in_row = {}

		for r in range(len(self.raw_rows)):
			row = self.raw_rows[r]
			buttons = len(row) / 2
			buttons_in_row[r] = buttons

			for j in range(buttons):

				row_height = r * distance_y + row_base_height

				circle_other = row_height - half_circle
				line_low = row_height + half_circle

				q = float(j) - float( buttons - 1) / 2
				x = self.width/2 + q * distance_x

				layout_output += " -draw \"circle %d,%d %d,%d\"" % (x ,row_height, x,circle_other)
				layout_output += " -draw \"line %d,%d %d,%d\"" % (x, circle_other, x, line_low)

		# Then draw the notes afterwards:
		for note in self.notes:
			basic = note.basic
			octave = note.octave
			push = note.isPress
			location_row = note.row_index
			location_button_index = note.button_index

			row_height = location_row * distance_y + row_base_height
			q = float(location_button_index) - float( buttons_in_row[location_row] - 1) / 2
			x = self.width/2 + q * distance_x

			text_x = x - center_x

			arc_start = 90
			arc_end = 270

			if push:
				basic_text_x = text_x - circle_size/4 + font_shift
				octave_text_x = text_x - octave_x + font_shift

			else:
				basic_text_x = text_x + circle_size/4 + font_shift
				octave_text_x = text_x + octave_x + font_shift
				arc_start = 270
				arc_end = 90

			text_extra += " -draw \"text %d,%d '%s'\"" % (basic_text_x,row_height - center_y, basic)
			text_small += " -draw \"text %d,%d '%s'\"" % (octave_text_x,row_height - center_y+octave_shift,octave)

			tup = (x - half_circle + font_label_width,row_height - half_circle, x + half_circle + font_label_width, row_height + half_circle, arc_start, arc_end)

			self.arc_lookup[note] = tup

		layout_output += text_extra
		layout_output += text_small

		layout_output += " layout.png"

		#print self.arc_lookup
		#for a,b in self.arc_lookup.items():
		#	print a,  b

		return [self.width, self.height, layout_output]

	def DrawChords(self):

		if not self.chords:
			return

		output_base = "convert -size %dx%d xc:transparent " % (self.width + font_label_width,self.height)
		output_base += " -stroke black -strokewidth 3 -draw \"line %d,%d %d,%d\" -draw \"line %d,%d %d,%d\" -draw \"line %d,%d %d,%d\"" % ( font_label_width, 0, font_label_width, height, 0, height, font_label_width + width, height, 0, 0, font_label_width + width, 0)

		chord_draw = []
		chord_files = []

		for chord in self.chords:
			name = chord[0][0]
			makeup = chord[0][1]

			# We may need to create up to 3 files depending on how we want this information to be displayed
			# We have Push, Pull and Arpeggio
			drawings = {"PUSH": "", "PULL": "", "ARP": ""}
			colour_indexes = {"PUSH": 0, "PULL": 0, "ARP": 0}

			has_non_arpeggio_solutions = False

			solutions = chord[1]
			for solution in solutions:
				snew = ""

				score = solution[0]
				typ = solution[1]
				notes = solution[2]

				if typ != "ARP":
					has_non_arpeggio_solutions = True

				if typ != "ARP" or includeArpeggios or (not has_non_arpeggio_solutions and not includeBackupArpeggiosOnly):
					c_index = colour_indexes[typ]
					col = colours[c_index]


					
					if (score < 0 and typ != "ARP") or (typ == "ARP" and has_non_arpeggio_solutions) or (typ == "ARP" and not has_non_arpeggio_solutions and score < -1000):
						col = "-fill \"rgb(200,200,200)\""
					else:
						colour_indexes[typ] = colour_indexes[typ] + 1

					#if name == "F +7":
						#print typ, score, has_non_arpeggio_solutions, col, notes

					snew = " %s" % col

					for note in notes:
						arc = self.arc_lookup[note]
						snew += " -draw \"arc %d,%d %d,%d %d,%d\"" % arc
					drawings[typ] += snew

			for key, data in drawings.items():
				snew = ""
				# Do we have any output for this chord:
				#print key, data
				#print chord[2]
				if data != "" or IncludeAllOutput:
					# Grey boxes for for loose notes:
					snew = " -fill \"rgb(200,200,200)\""
					for loose in chord[2][key]:
						arc = self.arc_lookup[loose]
						snew += " -draw \"arc %d,%d %d,%d %d,%d\"" % arc

				drawings[key] += snew

			for key, data in drawings.items():
				if data != "":
					chord_output = output_base
					# Write down what chord this is

					chord_output += " -stroke transparent -fill black -font Arial -pointsize 48 -gravity center -draw \"text %d,%d '%s'\" -draw \"text %d,%d '%s'\"" % ( - self.width / 2, -50, name + " " + key, -self.width / 2, 50, makeup)
					chord_output += " -gravity NorthWest"
					chord_output += data
					chord_output += " layout.png -geometry +%d+0 -composite -flatten \"%s.png\"" % (font_label_width, name + " " + key)

					chord_files.append(name + " " + key)

					drawings[key] = (chord_output)

			for data in drawings.values():
				if data != "":
					chord_draw.append(data)

		return (chord_draw, chord_files)




# Define the layout: We should be able to take this as a command line maybe?
row1 = ["F5","Eb5","D4","F#4","G4","A4","B4","C5","D5","E5",
		"G5","F#5","B5","A5","D6","C6","G6","E6","B6","F#6"]

row2 = ["G#4","Bb4","A3","C#4","D4","E4","F#4","G4","A4","B4",
		"D5","C#5","F#5","E5","A5","G5","D6","B5","F#6","C#6","A6","E6"]

row3 = []


### BC layout:

row1 = ["E3","A3", "G3","B3", "C4","D4", "E4","F4", "G4","A4",
	    "C5","B4", "E5","D5", "G5","F5", "C6","A5", "E6","B5"]
row2 = ["D#3","G#3", "F#3","A#3", "B3","C#4", "D#4","E4", "F#4","G#4", "B4","A#4",
        "D#5","C#5", "F#5","E5", "B5","G#5", "D#6","A#5", "F#6", "C#6"]



lay = Layout()
lay.AddRow(row1)
lay.AddRow(row2)


anchor_note = "G#"
circle_start_point = (semitones.index(anchor_note.upper())) % 12

output_order = (create_circle_of_fifths(circle_start_point))

chords = []
def create_chords(root_notes, chord_patterns):
	o = []
	for root_note in root_notes:
		for pattern in chord_patterns:
			name = pattern[0]
			offsets = pattern[1].split(",")
			chord = []
			semitone_number = semitone_lookup[root_note]
			for offset in offsets:
				chord.append(semitones[(semitone_number + int(offset)) % 12])

			root_name = root_note;
			if root_note in equivilents:
				root_name += "~" + equivilents[root_name]

			o.append(( "%s %s" % (root_name, name) , ','.join(chord) ) )

	return o

all_chords = create_chords(output_order,(
	("Major", "0,4,7"),
	("+7", "0,4,7,10"),
#	("+Maj7", "0,4,7,11"),
	("Minor", "0,3,7"),
#	("-7", "0,3,7,10"),
#	("-Maj7", "0,3,7,11"),
#	("I V", "0,7"),
#	("I +III", "0,4"),
#	("I -III", "0,3"),
#	("-III V", "4,7"),
#	("+III V", "3,7"),
	 ))

push_notes = []
pull_notes = []
all_notes = []

# Now let's generate information for the layout

lay.BuildChords(all_chords)


#convert -size 100x100 xc:skyblue -fill transparent -stroke black -draw "circle 50,30 50,10" -draw "line 50,10 50,50" -fill black -font Arial -draw "text 10,10 'Anthony'" circle.png
#convert -size 300x300 xc:skyblue -fill transparent -strokewidth 2 -stroke black -draw "circle 150,90 150,30" -draw "line 150,30 150,150" -fill black -font Arial -stroke transparent -pointsize 36 -gravity center -draw "text -27,-60 'A'" -draw "text 33,-60 'F#'" circle.png
#convert -size 300x300 xc:skyblue -fill transparent -strokewidth 2 -stroke black -draw "circle 150,90 150,30" -draw "line 150,30 150,150" -fill black -font Arial -stroke transparent -pointsize 36 -gravity center -draw "text -27,-60 'IIIIII'" -draw "text 32,-60 'IIIIII'" circle.png

circle_size = 120
distance_x = 150
distance_y = 120
x_border = 50
y_border = 50
font_shift = 2
octave_shift = 40
octave_x = 15
font_label_width = 500

chords_per_page = 9

layout_result = lay.DrawLayout()

width = layout_result[0]
height = layout_result[1]
layout_output = layout_result[2]


print layout_output

chord_draw_data = lay.DrawChords()
chord_draws = chord_draw_data[0]
chord_files = chord_draw_data[1]

for draw_string in chord_draws:
	print draw_string

# Generate pages:
succeeded = 0
remaining = chords_per_page
page_number = 1
page = ""
while succeeded == 0:

	remaining -= 1

	if chord_files:
		extra = chord_files[0]
		del chord_files[0]

		if remaining == chords_per_page - 1 and extra: 
			page = "convert \"%s.png\"" % (extra)
		else:
			page += " \"%s.png\" -append" % (extra)

	else:
		extra = "";

	if remaining == 0:
		if chord_files:
			page += " page%d.png" % (page_number)
			page_number += 1
			print page
			page = ""
			remaining = chords_per_page
		else:
			succeeded = 1

if page:
	page += " page%d.png" % (page_number)
	print page

#print layout_output
#print push_arc_lookup