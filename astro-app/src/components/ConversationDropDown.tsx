import { useState, useEffect } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu"

export default function ConversationDropDown() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSortChange = (sortType) => {
    console.log('Changing sort to:', sortType);
    
    if (window.ConversationUtils) {
      window.ConversationUtils.refreshConversationsDisplay(sortType);
    } else {
      console.error('ConversationUtils not available');
    }
  };

  if (!mounted) {
    return (
      <button className="menu-btn">
        <div className="menu-icon"></div>
      </button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="menu-btn">
          <div className="menu-icon"></div>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="custom-dropdown-content">
        <DropdownMenuLabel className="custom-dropdown-label">Trier tes conversations</DropdownMenuLabel>
        <DropdownMenuSeparator className="custom-dropdown-separator" />
        <DropdownMenuItem 
          className="custom-dropdown-item" 
          onClick={() => handleSortChange('date')}
        >
          par ordre croissant
        </DropdownMenuItem>
        <DropdownMenuItem 
          className="custom-dropdown-item"
          onClick={() => handleSortChange('oldest')}
        >
          par ordre décroissant
        </DropdownMenuItem>
        <DropdownMenuItem 
          className="custom-dropdown-item"
          onClick={() => handleSortChange('alphabetical')}
        >
          par nom
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}