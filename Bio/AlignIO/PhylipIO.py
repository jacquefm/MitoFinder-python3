# Copyright 2006-2013 by Peter Cock.  All rights reserved.
# Revisions copyright 2011 Brandon Invergo. All rights reserved.
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.
"""AlignIO support for "phylip" format from Joe Felsenstein's PHYLIP tools.

You are expected to use this module via the Bio.AlignIO functions (or the
Bio.SeqIO functions if you want to work directly with the gapped sequences).

Support for "relaxed phylip" format is also provided. Relaxed phylip differs
from standard phylip format in the following ways:

 * No whitespace is allowed in the sequence ID.
 * No truncation is performed. Instead, sequence IDs are padded to the longest
   ID length, rather than 10 characters. A space separates the sequence
   identifier from the sequence.

Relaxed phylip is supported by RAxML and PHYML.

Note
====
In TREE_PUZZLE (Schmidt et al. 2003) and PHYML (Guindon and Gascuel 2003)
a dot/period (".") in a sequence is interpreted as meaning the same
character as in the first sequence.  The PHYLIP documentation from 3.3 to 3.69
http://evolution.genetics.washington.edu/phylip/doc/sequence.html says:

   "a period was also previously allowed but it is no longer allowed,
   because it sometimes is used in different senses in other programs"

Biopython 1.58 or later treats dots/periods in the sequence as invalid, both
for reading and writing. Older versions did nothing special with a dot/period.
"""


import string

from Bio._py3k import range

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Align import MultipleSeqAlignment
from .Interfaces import AlignmentIterator, SequentialAlignmentWriter

_PHYLIP_ID_WIDTH = 10


class PhylipWriter(SequentialAlignmentWriter):
    """Phylip alignment writer."""

    def write_alignment(self, alignment, id_width=_PHYLIP_ID_WIDTH):
        """Use this to write (another) single alignment to an open file.

        This code will write interlaced alignments (when the sequences are
        longer than 50 characters).

        Note that record identifiers are strictly truncated to id_width,
        defaulting to the value required to comply with the PHYLIP standard.

        For more information on the file format, please see:
        http://evolution.genetics.washington.edu/phylip/doc/sequence.html
        http://evolution.genetics.washington.edu/phylip/doc/main.html#inputfiles
        """
        handle = self.handle

        if len(alignment) == 0:
            raise ValueError("Must have at least one sequence")
        length_of_seqs = alignment.get_alignment_length()
        for record in alignment:
            if length_of_seqs != len(record.seq):
                raise ValueError("Sequences must all be the same length")
        if length_of_seqs <= 0:
            raise ValueError("Non-empty sequences are required")

        # Check for repeated identifiers...
        # Apply this test *after* cleaning the identifiers
        names = []
        seqs = []
        for record in alignment:
            """
            Quoting the PHYLIP version 3.6 documentation:

            The name should be ten characters in length, filled out to
            the full ten characters by blanks if shorter. Any printable
            ASCII/ISO character is allowed in the name, except for
            parentheses ("(" and ")"), square brackets ("[" and "]"),
            colon (":"), semicolon (";") and comma (","). If you forget
            to extend the names to ten characters in length by blanks,
            the program [i.e. PHYLIP] will get out of synchronization
            with the contents of the data file, and an error message will
            result.

            Note that Tab characters count as only one character in the
            species names. Their inclusion can cause trouble.
            """
            name = record.id.strip()
            #Either remove the banned characters, or map them to something
            #else like an underscore "_" or pipe "|" character...
            for char in "[](),":
                name = name.replace(char, "")
            for char in ":;":
                name = name.replace(char, "|")
            name = name[:id_width]
            if name in names:
                raise ValueError("Repeated name %r (originally %r), "
                                 "possibly due to truncation"
                                 % (name, record.id))
            names.append(name)
            sequence = str(record.seq)
            if "." in sequence:
                # Do this check here (once per record, not once per block)
                raise ValueError("PHYLIP format no longer allows dots in "
                                 "sequence")
            seqs.append(sequence)

        # From experimentation, the use of tabs is not understood by the
        # EMBOSS suite.  The nature of the expected white space is not
        # defined in the PHYLIP documentation, simply "These are in free
        # format, separated by blanks".  We'll use spaces to keep EMBOSS
        # happy.
        handle.write(" %i %s\n" % (len(alignment), length_of_seqs))
        block = 0
        while True:
            for name, sequence in zip(names, seqs):
                if block == 0:
                    #Write name (truncated/padded to id_width characters)
                    #Now truncate and right pad to expected length.
                    handle.write(name[:id_width].ljust(id_width))
                else:
                    #write indent
                    handle.write(" " * id_width)
                #Write five chunks of ten letters per line...
                for chunk in range(0, 5):
                    i = block*50 + chunk*10
                    seq_segment = sequence[i:i+10]
                    #TODO - Force any gaps to be '-' character?  Look at the
                    #alphabet...
                    #TODO - How to cope with '?' or '.' in the sequence?
                    handle.write(" %s" % seq_segment)
                    if i+10 > length_of_seqs:
                        break
                handle.write("\n")
            block = block+1
            if block*50 > length_of_seqs:
                break
            handle.write("\n")


class PhylipIterator(AlignmentIterator):
    """Reads a Phylip alignment file returning a MultipleSeqAlignment iterator.

    Record identifiers are limited to at most 10 characters.

    It only copes with interlaced phylip files!  Sequential files won't work
    where the sequences are split over multiple lines.

    For more information on the file format, please see:
    http://evolution.genetics.washington.edu/phylip/doc/sequence.html
    http://evolution.genetics.washington.edu/phylip/doc/main.html#inputfiles
    """

    # Default truncation length
    id_width = _PHYLIP_ID_WIDTH

    def _is_header(self, line):
        line = line.strip()
        parts = [x for x in line.split() if x]
        if len(parts) != 2:
            return False  # First line should have two integers
        try:
            number_of_seqs = int(parts[0])
            length_of_seqs = int(parts[1])
            return True
        except ValueError:
            return False  # First line should have two integers

    def _split_id(self, line):
        """
        Extracts the sequence ID from a Phylip line, returning a tuple
        containing:

            (sequence_id, sequence_residues)

        The first 10 characters in the line are are the sequence id, the
        remainder are sequence data.
        """
        seq_id = line[:self.id_width].strip()
        seq = line[self.id_width:].strip().replace(' ', '')
        return seq_id, seq

    def __next__(self):
        handle = self.handle

        try:
            #Header we saved from when we were parsing
            #the previous alignment.
            line = self._header
            del self._header
        except AttributeError:
            line = handle.readline()

        if not line:
            raise StopIteration
        line = line.strip()
        parts = [x for x in line.split() if x]
        if len(parts) != 2:
            raise ValueError("First line should have two integers")
        try:
            number_of_seqs = int(parts[0])
            length_of_seqs = int(parts[1])
        except ValueError:
            raise ValueError("First line should have two integers")

        assert self._is_header(line)

        if self.records_per_alignment is not None \
        and self.records_per_alignment != number_of_seqs:
            raise ValueError("Found %i records in this alignment, told to expect %i"
                             % (number_of_seqs, self.records_per_alignment))

        ids = []
        seqs = []

        # By default, expects STRICT truncation / padding to 10 characters.
        # Does not require any whitespace between name and seq.
        for i in range(number_of_seqs):
            line = handle.readline().rstrip()
            sequence_id, s = self._split_id(line)
            ids.append(sequence_id)
            if "." in s:
                raise ValueError("PHYLIP format no longer allows dots in sequence")
            seqs.append([s])

        #Look for further blocks
        line = ""
        while True:
            #Skip any blank lines between blocks...
            while "" == line.strip():
                line = handle.readline()
                if not line:
                    break  # end of file
            if not line:
                break  # end of file

            if self._is_header(line):
                #Looks like the start of a concatenated alignment
                self._header = line
                break

            #print "New block..."
            for i in range(number_of_seqs):
                s = line.strip().replace(" ", "")
                if "." in s:
                    raise ValueError("PHYLIP format no longer allows dots in sequence")
                seqs[i].append(s)
                line = handle.readline()
                if (not line) and i+1 < number_of_seqs:
                    raise ValueError("End of file mid-block")
            if not line:
                break  # end of file

        records = (SeqRecord(Seq("".join(s), self.alphabet),
                             id=i, name=i, description=i)
                   for (i, s) in zip(ids, seqs))
        return MultipleSeqAlignment(records, self.alphabet)


# Relaxed Phylip
class RelaxedPhylipWriter(PhylipWriter):
    """
    Relaxed Phylip format writer
    """

    def write_alignment(self, alignment):
        """
        Write a relaxed phylip alignment
        """
        # Check inputs
        for name in (s.id.strip() for s in alignment):
            if any(c in name for c in string.whitespace):
                raise ValueError("Whitespace not allowed in identifier: %s"
                        % name)

        # Calculate a truncation length - maximum length of sequence ID plus a
        # single character for padding
        # If no sequences, set id_width to 1. super(...) call will raise a
        # ValueError
        if len(alignment) == 0:
            id_width = 1
        else:
            id_width = max((len(s.id.strip()) for s in alignment)) + 1
        super(RelaxedPhylipWriter, self).write_alignment(alignment, id_width)


class RelaxedPhylipIterator(PhylipIterator):
    """
    Relaxed Phylip format Iterator
    """

    def _split_id(self, line):
        """Returns the ID, sequence data from a line
        Extracts the sequence ID from a Phylip line, returning a tuple
        containing:

            (sequence_id, sequence_residues)

        For relaxed format - split at the first whitespace character
        """
        seq_id, sequence = line.split(None, 1)
        sequence = sequence.strip().replace(" ", "")
        return seq_id, sequence


class SequentialPhylipWriter(SequentialAlignmentWriter):
    """
    Sequential Phylip format Writer
    """
    def write_alignment(self, alignment, id_width=_PHYLIP_ID_WIDTH):
        handle = self.handle

        if len(alignment) == 0:
            raise ValueError("Must have at least one sequence")
        length_of_seqs = alignment.get_alignment_length()
        for record in alignment:
            if length_of_seqs != len(record.seq):
                raise ValueError("Sequences must all be the same length")
        if length_of_seqs <= 0:
            raise ValueError("Non-empty sequences are required")

        # Check for repeated identifiers...
        # Apply this test *after* cleaning the identifiers
        names = []
        for record in alignment:
            name = record.id.strip()
            #Either remove the banned characters, or map them to something
            #else like an underscore "_" or pipe "|" character...
            for char in "[](),":
                name = name.replace(char, "")
            for char in ":;":
                name = name.replace(char, "|")
            name = name[:id_width]
            if name in names:
                raise ValueError("Repeated name %r (originally %r), "
                                 "possibly due to truncation"
                                 % (name, record.id))
            names.append(name)

        # From experimentation, the use of tabs is not understood by the
        # EMBOSS suite.  The nature of the expected white space is not
        # defined in the PHYLIP documentation, simply "These are in free
        # format, separated by blanks".  We'll use spaces to keep EMBOSS
        # happy.
        handle.write(" %i %s\n" % (len(alignment), length_of_seqs))
        for name, record in zip(names, alignment):
            sequence = str(record.seq)
            if "." in sequence:
                raise ValueError("PHYLIP format no longer allows dots in "
                                 "sequence")
            handle.write(name[:id_width].ljust(id_width))
            # Write the entire sequence to one line (see sequential format
            # notes in the SequentialPhylipIterator docstring
            handle.write(sequence)
            handle.write("\n")


class SequentialPhylipIterator(PhylipIterator):
    """
    Sequential Phylip format Iterator

    The sequential format carries the same restrictions as the normal
    interleaved one, with the difference being that the sequences are listed
    sequentially, each sequence written in its entirety before the start of
    the next. According to the PHYLIP documentation for input file formatting,
    newlines and spaces may optionally be entered at any point in the sequences.
    """
    def __next__(self):
        handle = self.handle

        try:
            #Header we saved from when we were parsing
            #the previous alignment.
            line = self._header
            del self._header
        except AttributeError:
            line = handle.readline()

        if not line:
            raise StopIteration
        line = line.strip()
        parts = [x for x in line.split() if x]
        if len(parts) != 2:
            raise ValueError("First line should have two integers")
        try:
            number_of_seqs = int(parts[0])
            length_of_seqs = int(parts[1])
        except ValueError:
            raise ValueError("First line should have two integers")

        assert self._is_header(line)

        if self.records_per_alignment is not None \
        and self.records_per_alignment != number_of_seqs:
            raise ValueError("Found %i records in this alignment, told to expect %i"
                             % (number_of_seqs, self.records_per_alignment))

        ids = []
        seqs = []

        # By default, expects STRICT truncation / padding to 10 characters.
        # Does not require any whitespace between name and seq.
        for i in range(number_of_seqs):
            line = handle.readline().rstrip()
            sequence_id, s = self._split_id(line)
            ids.append(sequence_id)
            while len(s) < length_of_seqs:
                # The sequence may be split into multiple lines
                line = handle.readline().strip()
                if not line:
                    break
                if line == "":
                    continue
                s = "".join([s, line.strip().replace(" ", "")])
                if len(s) > length_of_seqs:
                    raise ValueError("Found a record of length %i, should be %i"
                            % (len(s), length_of_seqs))
            if "." in s:
                raise ValueError("PHYLIP format no longer allows dots in sequence")
            seqs.append(s)
        while True:
            # Find other alignments in the file
            line = handle.readline()
            if not line:
                break
            if self._is_header(line):
                self._header = line
                break

        records = (SeqRecord(Seq(s, self.alphabet),
                             id=i, name=i, description=i)
                   for (i, s) in zip(ids, seqs))
        return MultipleSeqAlignment(records, self.alphabet)


if __name__ == "__main__":
    print("Running short mini-test")

    phylip_text = """     8    286
V_Harveyi_ --MKNWIKVA VAAIA--LSA A--------- ---------T VQAATEVKVG
B_subtilis MKMKKWTVLV VAALLAVLSA CG-------- ----NGNSSS KEDDNVLHVG
B_subtilis MKKALLALFM VVSIAALAAC GAGNDNQSKD NAKDGDLWAS IKKKGVLTVG
YA80_HAEIN MKKLLFTTAL LTGAIAFSTF ---------- -SHAGEIADR VEKTKTLLVG
FLIY_ECOLI MKLAHLGRQA LMGVMAVALV AG---MSVKS FADEG-LLNK VKERGTLLVG
E_coli_Gln --MKSVLKVS LAALTLAFAV S--------- ---------S HAADKKLVVA
Deinococcu -MKKSLLSLK LSGLLVPSVL ALS------- -LSACSSPSS TLNQGTLKIA
HISJ_E_COL MKKLVLSLSL VLAFSSATAA F--------- ---------- AAIPQNIRIG

           MSGRYFPFTF VKQ--DKLQG FEVDMWDEIG KRNDYKIEYV TANFSGLFGL
           ATGQSYPFAY KEN--GKLTG FDVEVMEAVA KKIDMKLDWK LLEFSGLMGE
           TEGTYEPFTY HDKDTDKLTG YDVEVITEVA KRLGLKVDFK ETQWGSMFAG
           TEGTYAPFTF HDK-SGKLTG FDVEVIRKVA EKLGLKVEFK ETQWDAMYAG
           LEGTYPPFSF QGD-DGKLTG FEVEFAQQLA KHLGVEASLK PTKWDGMLAS
           TDTAFVPFEF KQG--DKYVG FDVDLWAAIA KELKLDYELK PMDFSGIIPA
           MEGTYPPFTS KNE-QGELVG FDVDIAKAVA QKLNLKPEFV LTEWSGILAG
           TDPTYAPFES KNS-QGELVG FDIDLAKELC KRINTQCTFV ENPLDALIPS

           LETGRIDTIS NQITMTDARK AKYLFADPYV VDG-AQITVR KGNDSIQGVE
           LQTGKLDTIS NQVAVTDERK ETYNFTKPYA YAG-TQIVVK KDNTDIKSVD
           LNSKRFDVVA NQVG-KTDRE DKYDFSDKYT TSR-AVVVTK KDNNDIKSEA
           LNAKRFDVIA NQTNPSPERL KKYSFTTPYN YSG-GVIVTK SSDNSIKSFE
           LDSKRIDVVI NQVTISDERK KKYDFSTPYT ISGIQALVKK GNEGTIKTAD
           LQTKNVDLAL AGITITDERK KAIDFSDGYY KSG-LLVMVK ANNNDVKSVK
           LQANKYDVIV NQVGITPERQ NSIGFSQPYA YSRPEIIVAK NNTFNPQSLA
           LKAKKIDAIM SSLSITEKRQ QEIAFTDKLY AADSRLVVAK NSDIQP-TVE

           DLAGKTVAVN LGSNFEQLLR DYDKDGKINI KTYDT--GIE HDVALGRADA
           DLKGKTVAAV LGSNHAKNLE SKDPDKKINI KTYETQEGTL KDVAYGRVDA
           DVKGKTSAQS LTSNYNKLAT N----AGAKV EGVEGMAQAL QMIQQARVDM
           DLKGRKSAQS ATSNWGKDAK A----AGAQI LVVDGLAQSL ELIKQGRAEA
           DLKGKKVGVG LGTNYEEWLR QNV--QGVDV RTYDDDPTKY QDLRVGRIDA
           DLDGKVVAVK SGTGSVDYAK AN--IKTKDL RQFPNIDNAY MELGTNRADA
           DLKGKRVGST LGSNYEKQLI DTG---DIKI VTYPGAPEIL ADLVAGRIDA
           SLKGKRVGVL QGTTQETFGN EHWAPKGIEI VSYQGQDNIY SDLTAGRIDA

           FIMDRLSALE -LIKKT-GLP LQLAGEPFET I-----QNAW PFVDNEKGRK
           YVNSRTVLIA -QIKKT-GLP LKLAGDPIVY E-----QVAF PFAKDDAHDK
           TYNDKLAVLN -YLKTSGNKN VKIAFETGEP Q-----STYF TFRKGS--GE
           TINDKLAVLD -YFKQHPNSG LKIAYDRGDK T-----PTAF AFLQGE--DA
           ILVDRLAALD -LVKKT-NDT LAVTGEAFSR Q-----ESGV ALRKGN--ED
           VLHDTPNILY -FIKTAGNGQ FKAVGDSLEA Q-----QYGI AFPKGS--DE
           AYNDRLVVNY -IINDQ-KLP VRGAGQIGDA A-----PVGI ALKKGN--SA
           AFQDEVAASE GFLKQPVGKD YKFGGPSVKD EKLFGVGTGM GLRKED--NE

           LQAEVNKALA EMRADGTVEK ISVKWFGADI TK----
           LRKKVNKALD ELRKDGTLKK LSEKYFNEDI TVEQKH
           VVDQVNKALK EMKEDGTLSK ISKKWFGEDV SK----
           LITKFNQVLE ALRQDGTLKQ ISIEWFGYDI TQ----
           LLKAVNDAIA EMQKDGTLQA LSEKWFGADV TK----
           LRDKVNGALK TLRENGTYNE IYKKWFGTEP K-----
           LKDQIDKALT EMRSDGTFEK ISQKWFGQDV GQP---
           LREALNKAFA EMRADGTYEK LAKKYFDFDV YGG---
"""

    from Bio._py3k import StringIO
    handle = StringIO(phylip_text)
    count = 0
    for alignment in PhylipIterator(handle):
        for record in alignment:
            count = count+1
            print(record.id)
            #print str(record.seq)
    assert count == 8

    expected = """mkklvlslsl vlafssataa faaipqniri gtdptyapfe sknsqgelvg
    fdidlakelc krintqctfv enpldalips lkakkidaim sslsitekrq qeiaftdkly
    aadsrlvvak nsdiqptves lkgkrvgvlq gttqetfgne hwapkgieiv syqgqdniys
    dltagridaafqdevaaseg flkqpvgkdy kfggpsvkde klfgvgtgmg lrkednelre
    alnkafaemradgtyeklak kyfdfdvygg""".replace(" ", "").replace("\n", "").upper()
    assert str(record.seq).replace("-", "") == expected

    #From here:
    #http://atgc.lirmm.fr/phyml/usersguide.html
    phylip_text2 = """5 60
Tax1        CCATCTCACGGTCGGTACGATACACCTGCTTTTGGCAG
Tax2        CCATCTCACGGTCAGTAAGATACACCTGCTTTTGGCGG
Tax3        CCATCTCCCGCTCAGTAAGATACCCCTGCTGTTGGCGG
Tax4        TCATCTCATGGTCAATAAGATACTCCTGCTTTTGGCGG
Tax5        CCATCTCACGGTCGGTAAGATACACCTGCTTTTGGCGG

GAAATGGTCAATATTACAAGGT
GAAATGGTCAACATTAAAAGAT
GAAATCGTCAATATTAAAAGGT
GAAATGGTCAATCTTAAAAGGT
GAAATGGTCAATATTAAAAGGT"""

    phylip_text3 = """5 60
Tax1        CCATCTCACGGTCGGTACGATACACCTGCTTTTGGCAGGAAATGGTCAATATTACAAGGT
Tax2        CCATCTCACGGTCAGTAAGATACACCTGCTTTTGGCGGGAAATGGTCAACATTAAAAGAT
Tax3        CCATCTCCCGCTCAGTAAGATACCCCTGCTGTTGGCGGGAAATCGTCAATATTAAAAGGT
Tax4        TCATCTCATGGTCAATAAGATACTCCTGCTTTTGGCGGGAAATGGTCAATCTTAAAAGGT
Tax5        CCATCTCACGGTCGGTAAGATACACCTGCTTTTGGCGGGAAATGGTCAATATTAAAAGGT"""

    handle = StringIO(phylip_text2)
    list2 = list(PhylipIterator(handle))
    handle.close()
    assert len(list2) == 1
    assert len(list2[0]) == 5

    handle = StringIO(phylip_text3)
    list3 = list(PhylipIterator(handle))
    handle.close()
    assert len(list3) == 1
    assert len(list3[0]) == 5

    for i in range(0, 5):
        list2[0][i].id == list3[0][i].id
        str(list2[0][i].seq) == str(list3[0][i].seq)

    #From here:
    #http://evolution.genetics.washington.edu/phylip/doc/sequence.html
    #Note the lack of any white space between names 2 and 3 and their seqs.
    phylip_text4 = """  5    42
Turkey    AAGCTNGGGC ATTTCAGGGT
Salmo gairAAGCCTTGGC AGTGCAGGGT
H. SapiensACCGGTTGGC CGTTCAGGGT
Chimp     AAACCCTTGC CGTTACGCTT
Gorilla   AAACCCTTGC CGGTACGCTT

GAGCCCGGGC AATACAGGGT AT
GAGCCGTGGC CGGGCACGGT AT
ACAGGTTGGC CGTTCAGGGT AA
AAACCGAGGC CGGGACACTC AT
AAACCATTGC CGGTACGCTT AA"""

    #From here:
    #http://evolution.genetics.washington.edu/phylip/doc/sequence.html
    phylip_text5 = """  5    42
Turkey    AAGCTNGGGC ATTTCAGGGT
GAGCCCGGGC AATACAGGGT AT
Salmo gairAAGCCTTGGC AGTGCAGGGT
GAGCCGTGGC CGGGCACGGT AT
H. SapiensACCGGTTGGC CGTTCAGGGT
ACAGGTTGGC CGTTCAGGGT AA
Chimp     AAACCCTTGC CGTTACGCTT
AAACCGAGGC CGGGACACTC AT
Gorilla   AAACCCTTGC CGGTACGCTT
AAACCATTGC CGGTACGCTT AA"""

    phylip_text5a = """  5    42
Turkey    AAGCTNGGGC ATTTCAGGGT GAGCCCGGGC AATACAGGGT AT
Salmo gairAAGCCTTGGC AGTGCAGGGT GAGCCGTGGC CGGGCACGGT AT
H. SapiensACCGGTTGGC CGTTCAGGGT ACAGGTTGGC CGTTCAGGGT AA
Chimp     AAACCCTTGC CGTTACGCTT AAACCGAGGC CGGGACACTC AT
Gorilla   AAACCCTTGC CGGTACGCTT AAACCATTGC CGGTACGCTT AA"""

    handle = StringIO(phylip_text4)
    list4 = list(PhylipIterator(handle))
    handle.close()
    assert len(list4) == 1
    assert len(list4[0]) == 5

    handle = StringIO(phylip_text5)
    try:
        list5 = list(PhylipIterator(handle))
        assert len(list5) == 1
        assert len(list5[0]) == 5
        print("That should have failed...")
    except ValueError:
        print("Evil multiline non-interlaced example failed as expected")
    handle.close()

    handle = StringIO(phylip_text5a)
    list5 = list(PhylipIterator(handle))
    handle.close()
    assert len(list5) == 1
    assert len(list4[0]) == 5

    print("Concatenation")
    handle = StringIO(phylip_text4 + "\n" + phylip_text4)
    assert len(list(PhylipIterator(handle))) == 2

    handle = StringIO(phylip_text3 + "\n" + phylip_text4 + "\n\n\n" + phylip_text)
    assert len(list(PhylipIterator(handle))) == 3

    print("OK")

    print("Checking write/read")
    handle = StringIO()
    PhylipWriter(handle).write_file(list5)
    handle.seek(0)
    list6 = list(PhylipIterator(handle))
    assert len(list5) == len(list6)
    for a1, a2 in zip(list5, list6):
        assert len(a1) == len(a2)
        for r1, r2 in zip(a1, a2):
            assert r1.id == r2.id
            assert str(r1.seq) == str(r2.seq)
    print("Done")
