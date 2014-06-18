# -*- encoding: utf-8 -*-
from supriya.tools.ugentools.Delay1 import Delay1


class Delay2(Delay1):
    r'''Two-sample delay line unit generator.

    ::

        >>> from supriya.tools import ugentools
        >>> source = ugentools.In.ar(bus=0)
        >>> ugentools.Delay2.ar(source=source)
        Delay2.ar()

    '''

    ### CLASS VARIABLES ###

    __slots__ = ()

    ### PUBLIC METHODS ###

    @classmethod
    def ar(
        cls,
        delay_time=0.2,
        maximum_delay_time=0.2,
        source=None,
        ):
        r'''Create an audio-rate two-sample delay line.

        ::

            >>> from supriya.tools import ugentools
            >>> source = ugentools.In.ar(bus=0)
            >>> ugentools.Delay2.ar(
            ...     source=source,
            ...     )
            Delay2.ar()

        Returns unit generator graph.
        '''
        return super(Delay2, cls).ar(
            source=source,
            )

    @classmethod
    def kr(
        cls,
        source=None,
        ):
        r'''Create a control-rate two-sample delay line.

        ::

            >>> from supriya.tools import ugentools
            >>> source = ugentools.In.kr(bus=0)
            >>> ugentools.Delay2.kr(
            ...     source=source,
            ...     )
            Delay2.ar()

        Returns unit generator graph.
        '''
        return super(Delay2, cls).kr(
            source=source,
            )
