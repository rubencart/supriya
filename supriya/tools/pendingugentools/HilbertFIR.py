# -*- encoding: utf-8 -*-
from supriya.tools.synthdeftools.UGen import UGen


class HilbertFIR(UGen):
    r'''

    ::

        >>> hilbert_fir = ugentools.HilbertFIR.(
        ...     buffer_id=None,
        ...     source=None,
        ...     )
        >>> hilbert_fir

    '''

    ### CLASS VARIABLES ###

    __documentation_section__ = None

    __slots__ = ()

    _ordered_input_names = (
        'source',
        'buffer_id',
        )

    _valid_calculation_rates = None

    ### INITIALIZER ###

    def __init__(
        self,
        calculation_rate=None,
        buffer_id=None,
        source=None,
        ):
        UGen.__init__(
            self,
            calculation_rate=calculation_rate,
            buffer_id=buffer_id,
            source=source,
            )

    ### PUBLIC METHODS ###

    @classmethod
    def ar(
        cls,
        buffer_id=None,
        source=None,
        ):
        r'''Constructs an audio-rate HilbertFIR.

        ::

            >>> hilbert_fir = ugentools.HilbertFIR.ar(
            ...     buffer_id=None,
            ...     source=None,
            ...     )
            >>> hilbert_fir

        Returns ugen graph.
        '''
        from supriya.tools import synthdeftools
        calculation_rate = synthdeftools.CalculationRate.AUDIO
        ugen = cls._new_expanded(
            calculation_rate=calculation_rate,
            buffer_id=buffer_id,
            source=source,
            )
        return ugen

    ### PUBLIC PROPERTIES ###

    @property
    def buffer_id(self):
        r'''Gets `buffer_id` input of HilbertFIR.

        ::

            >>> hilbert_fir = ugentools.HilbertFIR.ar(
            ...     buffer_id=None,
            ...     source=None,
            ...     )
            >>> hilbert_fir.buffer_id

        Returns ugen input.
        '''
        index = self._ordered_input_names.index('buffer_id')
        return self._inputs[index]

    @property
    def source(self):
        r'''Gets `source` input of HilbertFIR.

        ::

            >>> hilbert_fir = ugentools.HilbertFIR.ar(
            ...     buffer_id=None,
            ...     source=None,
            ...     )
            >>> hilbert_fir.source

        Returns ugen input.
        '''
        index = self._ordered_input_names.index('source')
        return self._inputs[index]