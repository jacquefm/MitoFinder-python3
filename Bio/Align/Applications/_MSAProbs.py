# Copyright 2013 by Christian Brueffer. All rights reserved.
#
# This code is part of the Biopython distribution and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.
"""Command line wrapper for the multiple sequence alignment program MSAProbs.
"""



__docformat__ = "epytext en"  # Don't just use plain text in epydoc API pages!

from Bio.Application import _Argument, _Option, _Switch, AbstractCommandline


class MSAProbsCommandline(AbstractCommandline):
    """Command line wrapper for MSAProbs.

    http://msaprobs.sourceforge.net

    Example:

    >>> from Bio.Align.Applications import MSAProbsCommandline
    >>> in_file = "unaligned.fasta"
    >>> out_file = "aligned.cla"
    >>> cline = MSAProbsCommandline(infile=in_file, outfile=out_file, clustalw=True)
    >>> print(cline)
    msaprobs -o aligned.cla -clustalw unaligned.fasta

    You would typically run the command line with cline() or via
    the Python subprocess module, as described in the Biopython tutorial.

    Citation:

    Yongchao Liu, Bertil Schmidt, Douglas L. Maskell: "MSAProbs: multiple
    sequence alignment based on pair hidden Markov models and partition
    function posterior probabilities". Bioinformatics, 2010, 26(16): 1958 -1964

    Last checked against version: 0.9.7
    """

    def __init__(self, cmd="msaprobs", **kwargs):
        # order of parameters is the same as in msaprobs -help
        self.parameters = \
            [
            _Option(["-o", "--outfile", "outfile"],
                    "specify the output file name (STDOUT by default)",
                    filename=True,
                    equate=False),
            _Option(["-num_threads", "numthreads"],
                    "specify the number of threads used, and otherwise detect automatically",
                    checker_function=lambda x: isinstance(x, int)),
            _Switch(["-clustalw", "clustalw"],
                    "use CLUSTALW output format instead of FASTA format"),
            _Option(["-c", "consistency"],
                    "use 0 <= REPS <= 5 (default: 2) passes of consistency transformation",
                    checker_function=lambda x: isinstance(x, int) and 0 <= x <= 5),
            _Option(["-ir", "--iterative-refinement", "iterative_refinement"],
                    "use 0 <= REPS <= 1000 (default: 10) passes of iterative-refinement",
                    checker_function=lambda x: isinstance(x, int) and 0 <= x <= 1000),
            _Switch(["-v", "verbose"],
                    "report progress while aligning (default: off)"),
            _Option(["-annot", "annot"],
                    "write annotation for multiple alignment to FILENAME",
                    filename=True),
            _Switch(["-a", "--alignment-order", "alignment_order"],
                    "print sequences in alignment order rather than input order (default: off)"),
            _Option(["-version", "version"],
                    "print out version of MSAPROBS"),
            _Argument(["infile"],
                    "Multiple sequence input file",
                    filename=True),
            ]
        AbstractCommandline.__init__(self, cmd, **kwargs)


def _test():
    """Run the module's doctests (PRIVATE)."""
    print("Running MSAProbs doctests...")
    import doctest
    doctest.testmod()
    print("Done")


if __name__ == "__main__":
    _test()
