from enum import Enum


class RacingReferenceCode(Enum):
    GRAND_AM = 'GA'
    QUALIFIER = 'Q'
    CAMPING_WORLD_TRUCK_SERIES = 'C'
    NATIONWIDE_SERIES = 'B'
    SPRINT_CUP = 'W'
    MODIFIED_SOUTHERN_TOUR = 'M'
    NASCAR_K_AND_N_PRO_SERIES_EAST = 'E'
    ALL_STAR = 'S'
    NASCAR_CANADIAN_TIRE_SERIES = 'T'
    NASCAR_K_AND_N_PRO_SERIES_WEST = 'P'
    MODIFIED_TOUR = 'N'
    NASCAR_TOYOTA_SERIES = 'MX'
    NASCAR_MONSTER_ENERGY_GRAND_PRIX = 'M2'

    @classmethod
    def is_regular_season(cls, end_string):
        if end_string == cls.SPRINT_CUP.value\
                or end_string == cls.ALL_STAR.value:
            return True
        elif end_string in [code.value for code in RacingReferenceCode]:
            return False
        else:
            raise Exception('Unexpected code: ' + end_string)


