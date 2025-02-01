import enum
from sqlalchemy import Enum

class StateNameEnum(enum.Enum):
    ABIA = 'Abia'
    ADAMAWA = 'Adamawa'
    AKWA_IBOM = 'Akwa Ibom'
    ANAMBRA = 'Anambra'
    BAUCHI = 'Bauchi'
    BAYELSA = 'Bayelsa'
    BENUE = 'Benue'
    BORNO = 'Borno'
    CROSS_RIVER = 'Cross River'
    DELTA = 'Delta'
    EBONYI = 'Ebonyi'
    EDO = 'Edo'
    EKITI = 'Ekiti'
    ENUGU = 'Enugu'
    FCT = 'Fct'
    GOMBE = 'Gombe'
    IMO = 'Imo'
    JIGAWA = 'Jigawa'
    KADUNA = 'Kaduna'
    KANO = 'Kano'
    KATSINA = 'Katsina'
    KEBBI = 'Kebbi'
    KOGI = 'Kogi'
    KWARA = 'Kwara'
    LAGOS = 'Lagos'
    NASARAWA = 'Nasarawa'
    NIGER = 'Niger'
    OGUN = 'Ogun'
    ONDO = 'Ondo'
    OSUN = 'Osun'
    OYO = 'Oyo'
    PLATEAU = 'Plateau'
    RIVERS = 'Rivers'
    SOKOTO = 'Sokoto'
    TARABA = 'Taraba'
    YOBE = 'Yobe'
    ZAMFARA = 'Zamfara'
    

class RegionEnum(enum.Enum):
    NORTH_CENTRAL = 'North Central'
    NORTH_EAST = 'North East'
    NORTH_WEST = 'North West'
    SOUTH_EAST = 'South East'
    SOUTH_SOUTH = 'South South'
    SOUTH_WEST = 'South West'
    
     

