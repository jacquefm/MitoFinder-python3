# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.
#

"""Command line wrapper for bwa
"""


from Bio._py3k import str

__docformat__ = "epytext en"

from Bio.Application import _Option, _Argument, _Switch, AbstractCommandline
from Bio.Application import _StaticArgument


class BwaIndexCommandline(AbstractCommandline):
    """Command line wrapper for Burrows Wheeler Aligner (BWA) index.

    Index database sequences in the FASTA format, equivalent to::

        $ bwa index [-p prefix] [-a algoType] [-c] <in.db.fasta>

    See http://bio-bwa.sourceforge.net/bwa.shtml for details.

    Example:

    >>> from Bio.Sequencing.Applications import BwaIndexCommandline
    >>> reference_genome = "/path/to/reference_genome.fasta"
    >>> index_cmd = BwaIndexCommandline(infile=reference_genome, algorithm="bwtsw")
    >>> print(index_cmd)
    bwa index -a bwtsw /path/to/reference_genome.fasta

    You would typically run the command using index_cmd() or via the
    Python subprocess module, as described in the Biopython tutorial.

    """
    def __init__(self, cmd="bwa", **kwargs):
        self.program_name = cmd
        self.parameters = \
                [
                    _StaticArgument("index"),
                    _Option(["-a", "a", "algorithm"],
                            """Algorithm for constructing BWT index.

                            Available options are:
                             - is:    IS linear-time algorithm for constructing suffix array.
                                      It requires 5.37N memory where N is the size of the database.
                                      IS is moderately fast, but does not work with database larger
                                      than 2GB. IS is the default algorithm due to its simplicity.
                             - bwtsw: Algorithm implemented in BWT-SW. This method works with the
                                      whole human genome, but it does not work with database
                                      smaller than 10MB and it is usually slower than IS.""",
                            checker_function=lambda x: x in ["is", "bwtsw"],
                            equate=False, is_required=True),
                    _Option(["-p", "p", "prefix"],
                            "Prefix of the output database [same as db filename]",
                            equate=False, is_required=False),
                    _Argument(["infile"], "Input file name", filename=True, is_required=True),
                    _Switch(["-c", "c"],
                            "Build color-space index. The input fasta should be in nucleotide space.")
                ]
        AbstractCommandline.__init__(self, cmd, **kwargs)


class BwaAlignCommandline(AbstractCommandline):
    """Command line wrapper for Burrows Wheeler Aligner (BWA) aln.

    Run a BWA alignment, equivalent to::

        $ bwa aln [...] <in.db.fasta> <in.query.fq> > <out.sai>

    See http://bio-bwa.sourceforge.net/bwa.shtml for details.

    Example:

    >>> from Bio.Sequencing.Applications import BwaAlignCommandline
    >>> reference_genome = "/path/to/reference_genome.fasta"
    >>> read_file = "/path/to/read_1.fq"
    >>> output_sai_file = "/path/to/read_1.sai"
    >>> read_group="@RG\tID:foo\tSM:bar"
    >>> align_cmd = BwaAlignCommandline(reference=reference_genome, read_file=read_file)
    >>> print(align_cmd)
    bwa aln /path/to/reference_genome.fasta /path/to/read_1.fq

    You would typically run the command line using align_cmd(stdout=output_sai_file)
    or via the Python subprocess module, as described in the Biopython tutorial.
    """
    def __init__(self, cmd="bwa", **kwargs):
        self.program_name = cmd
        self.parameters = \
                [
                    _StaticArgument("aln"),
                    _Argument(["reference"], "Reference file name",
                              filename=True, is_required=True),
                    _Argument(["read_file"], "Read file name",
                              filename=True, is_required=True),
                    _Option(["-n", "n"],
                            "Maximum edit distance if the value is INT, or the fraction of missing alignments given 2% uniform base error rate if FLOAT. In the latter case, the maximum edit distance is automatically chosen for different read lengths. [0.04]",
                            checker_function=lambda x: isinstance(x, (int, float)),
                            equate=False),
                    _Option(["-o", "o"],
                            "Maximum edit distance if the value is INT, or the fraction of missing alignments given 2% uniform base error rate if FLOAT. In the latter case, the maximum edit distance is automatically chosen for different read lengths. [0.04]",
                            checker_function=lambda x: isinstance(x, (int, float)),
                            equate=False),
                    _Option(["-e", "e"],
                            "Maximum number of gap extensions, -1 for k-difference mode (disallowing long gaps) [-1]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-d", "d"],
                            "Disallow a long deletion within INT bp towards the 3-end [16]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-i", "i"],
                            "Disallow an indel within INT bp towards the ends [5]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-l", "l"],
                            """Take the first INT subsequence as seed.

                            If INT is larger than the query sequence, seeding will be disabled.
                            For long reads, this option is typically ranged from 25 to 35 for
                            -k 2. [inf]""",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-k", "k"], "Maximum edit distance in the seed [2]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-t", "t"], "Number of threads (multi-threading mode) [1]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-M", "M"],
                            "Mismatch penalty. BWA will not search for suboptimal hits with a score lower than (bestScore-misMsc). [3]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-O", "O"], "Gap open penalty [11]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-E", "E"], "Gap extension penalty [4]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-R", "R"],
                            """Proceed with suboptimal alignments if there are no more than INT equally best hits.

                            This option only affects paired-end mapping. Increasing this threshold helps
                            to improve the pairing accuracy at the cost of speed, especially for short
                            reads (~32bp).""",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-q", "q"],
                            """Parameter for read trimming [0].

                            BWA trims a read down to argmax_x{\sum_{i=x+1}^l(INT-q_i)} if q_l<INT
                            where l is the original read length.""",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-B", "B"],
                            "Length of barcode starting from the 5-end. When INT is positive, the barcode of each read will be trimmed before mapping and will be written at the BC SAM tag. For paired-end reads, the barcode from both ends are concatenated. [0]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Switch(["-c", "c"],
                            "Reverse query but not complement it, which is required for alignment in the color space."),
                    _Switch(["-N", "N"],
                            "Disable iterative search. All hits with no more than maxDiff differences will be found. This mode is much slower than the default."),
                    _Switch(["-I", "I"],
                            "The input is in the Illumina 1.3+ read format (quality equals ASCII-64)."),
                    _Switch(["-b", "b"],
                            "Specify the input read sequence file is the BAM format"),
                    _Switch(["-b1", "b1"],
                            "When -b is specified, only use the first read in a read pair in mapping (skip single-end reads and the second reads)."),
                    _Switch(["-b2", "b2"],
                            "When -b is specified, only use the second read in a read pair in mapping.")
                  ]
        AbstractCommandline.__init__(self, cmd, **kwargs)


class BwaSamseCommandline(AbstractCommandline):
    """Command line wrapper for Burrows Wheeler Aligner (BWA) samse.

    Generate alignments in the SAM format given single-end reads.
    Equvialent to::

        $ bwa samse [-n maxOcc] <in.db.fasta> <in.sai> <in.fq> > <out.sam>

    See http://bio-bwa.sourceforge.net/bwa.shtml for details.

    Example:

    >>> from Bio.Sequencing.Applications import BwaSamseCommandline
    >>> reference_genome = "/path/to/reference_genome.fasta"
    >>> read_file = "/path/to/read_1.fq"
    >>> sai_file = "/path/to/read_1.sai"
    >>> output_sam_file = "/path/to/read_1.sam"
    >>> samse_cmd = BwaSamseCommandline(reference=reference_genome,
    ...                                 read_file=read_file, sai_file=sai_file)
    >>> print(samse_cmd)
    bwa samse /path/to/reference_genome.fasta /path/to/read_1.sai /path/to/read_1.fq

    You would typically run the command line using samse_cmd(stdout=output_sam_file)
    or via the Python subprocess module, as described in the Biopython tutorial.
    """
    def __init__(self, cmd="bwa", **kwargs):
        self.program_name = cmd
        self.parameters = \
                [
                    _StaticArgument("samse"),
                    _Argument(["reference"], "Reference file name", filename=True, is_required=True),
                    _Argument(["sai_file"], "Sai file name", filename=True, is_required=True),
                    _Argument(["read_file"], "Read  file name", filename=True, is_required=True),
                    _Option(["-n", "n"],
                            """Maximum number of alignments to output in the XA tag for reads paired properly.

                            If a read has more than INT hits, the XA tag will not be written. [3]""",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-r", "r"],
                            "Specify the read group in a format like '@RG\tID:foo\tSM:bar'. [null]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                  ]
        AbstractCommandline.__init__(self, cmd, **kwargs)


class BwaSampeCommandline(AbstractCommandline):
    """Command line wrapper for Burrows Wheeler Aligner (BWA) sampe.

    Generate alignments in the SAM format given paired-end reads. 
    Equivalent to::

        $ bwa sampe [...] <in.db.fasta> <in1.sai> <in2.sai> <in1.fq> <in2.fq> > <out.sam>

    See http://bio-bwa.sourceforge.net/bwa.shtml for details.

    Example:

    >>> from Bio.Sequencing.Applications import BwaSampeCommandline
    >>> reference_genome = "/path/to/reference_genome.fasta"
    >>> read_file1 = "/path/to/read_1.fq"
    >>> read_file2 = "/path/to/read_2.fq"
    >>> sai_file1 = "/path/to/read_1.sai"
    >>> sai_file2 = "/path/to/read_2.sai"
    >>> output_sam_file = "/path/to/output.sam"
    >>> read_group = "@RG\tID:foo\tSM:bar"
    >>> sampe_cmd = BwaSampeCommandline(reference=reference_genome,
    ...                                 sai_file1=sai_file1, sai_file2=sai_file2,
    ...                                 read_file1=read_file1, read_file2=read_file2,
    ...                                 r=read_group)
    >>> print(sampe_cmd)
    bwa sampe /path/to/reference_genome.fasta /path/to/read_1.sai /path/to/read_2.sai /path/to/read_1.fq /path/to/read_2.fq -r @RG       ID:foo  SM:bar

    You would typically run the command line using sampe_cmd(stdout=output_sam_file)
    or via the Python subprocess module, as described in the Biopython tutorial.
    """
    #TODO - Should the read group have a raw tab in it, or \t?
    def __init__(self, cmd="bwa", **kwargs):
        self.program_name = cmd
        self.parameters = \
                [
                    _StaticArgument("sampe"),
                    _Argument(["reference"], "Reference file name", filename=True, is_required=True),
                    _Argument(["sai_file1"], "Sai file 1", filename=True, is_required=True),
                    _Argument(["sai_file2"], "Sai file 2", filename=True, is_required=True),
                    _Argument(["read_file1"], "Read  file 1", filename=True, is_required=True),
                    _Argument(["read_file2"], "Read  file 2", filename=True, is_required=True),
                    _Option(["-a", "a"],
                            """Maximum insert size for a read pair to be considered being mapped properly [500].

                            Since 0.4.5, this option is only used when there are not enough
                            good alignments to infer the distribution of insert sizes.""",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-o", "o"],
                            """Maximum occurrences of a read for pairing [100000].

                            A read with more occurrences will be treated as a single-end read.
                            Reducing this parameter helps faster pairing.""",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-n", "n"],
                            """Maximum number of alignments to output in the XA tag for reads paired properly [3].

                            If a read has more than INT hits, the XA tag will not be written.""",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-N", "N"],
                            """Maximum number of alignments to output in the XA tag for disconcordant read pairs (excluding singletons) [10].

                         .  If a read has more than INT hits, the XA tag will not be written.""",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-r", "r"], "Specify the read group in a format like '@RG\tID:foo\tSM:bar'. [null]",
                            checker_function=lambda x: isinstance(x, str),
                            equate=False),
                  ]
        AbstractCommandline.__init__(self, cmd, **kwargs)


class BwaBwaswCommandline(AbstractCommandline):
    """Command line wrapper for Burrows Wheeler Aligner (BWA) bwasw.

    Align query sequences from FASTQ files. Equivalent to::

        $ bwa bwasw [...] <in.db.fasta> <in.fq>

    See http://bio-bwa.sourceforge.net/bwa.shtml for details.

    Example:

    >>> from Bio.Sequencing.Applications import BwaBwaswCommandline
    >>> reference_genome = "/path/to/reference_genome.fasta"
    >>> read_file = "/path/to/read_1.fq"
    >>> bwasw_cmd = BwaBwaswCommandline(reference=reference_genome, read_file=read_file)
    >>> print(bwasw_cmd)
    bwa bwasw /path/to/reference_genome.fasta /path/to/read_1.fq

    You would typically run the command line using bwasw_cmd() or via the
    Python subprocess module, as described in the Biopython tutorial.
    """
    def __init__(self, cmd="bwa", **kwargs):
        self.program_name = cmd
        self.parameters = \
                [
                    _StaticArgument("bwasw"),
                    _Argument(["reference"], "Reference file name", filename=True, is_required=True),
                    _Argument(["read_file"], "Read file", filename=True, is_required=True),
                    _Argument(["mate_file"], "Mate file", filename=True, is_required=False),
                    _Option(["-a", "a"],
                            "Score of a match [1]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-b", "b"],
                            "Mismatch penalty [3]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-q", "q"],
                            "Gap open penalty [5]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-r", "r"],
                            "Gap extension penalty. The penalty for a contiguous gap of size k is q+k*r. [2]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-t", "t"],
                            "Number of threads in the multi-threading mode [1]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-w", "w"],
                            "Band width in the banded alignment [33]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-T", "T"],
                            "Minimum score threshold divided by a [37]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-c", "c"],
                            """Coefficient for threshold adjustment according to query length [5.5].

                            Given an l-long query, the threshold for a hit to be retained is
                            a*max{T,c*log(l)}.""",
                            checker_function=lambda x: isinstance(x, float),
                            equate=False),
                    _Option(["-z", "z"],
                            "Z-best heuristics. Higher -z increases accuracy at the cost of speed. [1]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-s", "s"],
                            """Maximum SA interval size for initiating a seed [3].

                            Higher -s increases accuracy at the cost of speed.""",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                    _Option(["-N", "N"],
                            "Minimum number of seeds supporting the resultant alignment to skip reverse alignment. [5]",
                            checker_function=lambda x: isinstance(x, int),
                            equate=False),
                  ]
        AbstractCommandline.__init__(self, cmd, **kwargs)


def _test():
        """Run the module's doctests (PRIVATE)."""
        print("Running modules doctests...")
        import doctest
        doctest.testmod()
        print("Done")


if __name__ == "__main__":
    _test()
