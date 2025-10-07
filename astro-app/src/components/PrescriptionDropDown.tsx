import { useState, useEffect } from 'react';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "./ui/dropdown-menu"

export default function PrescriptionDropDown() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const handleSortChange = (dir: 'asc' | 'desc') => {
    if (window.PrescriptionPageUtils?.sortPrescriptions) {
      window.PrescriptionPageUtils.sortPrescriptions(dir);
    } else {
      console.error('PrescriptionPageUtils not available');
    }
  };

  if (!mounted) {
    return <button className="menu-btn"><div className="menu-icon"></div></button>;
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="menu-btn"><div className="menu-icon"></div></button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="custom-dropdown-content">
        <DropdownMenuLabel className="custom-dropdown-label">
          Trier tes ordonnances
        </DropdownMenuLabel>
        <DropdownMenuSeparator className="custom-dropdown-separator" />
        <DropdownMenuItem className="custom-dropdown-item" onClick={() => handleSortChange('asc')}>
          par date croissante
        </DropdownMenuItem>
        <DropdownMenuItem className="custom-dropdown-item" onClick={() => handleSortChange('desc')}>
          par date décroissante
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
